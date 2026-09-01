"""Build a versioned data-only patch. Never connects to a database.

Run with the bundled Python and PYTHONPATH=/private/tmp/d13_pydeps.
The released D13 folder is immutable input. Generated SQL defaults to ROLLBACK.
"""
from pathlib import Path
from collections import Counter, defaultdict
import csv
import hashlib
import json
import shutil
import sys

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent
SOURCE = PROJECT / 'ReRouteHer_D13_MASCO2020_2026-08-30'
LEGACY = PROJECT / 'ReRouteHer_DataTeam_Fresh_HighStandard_2026-08-27/01_REFERENCE_TABLES'
sys.path.insert(0, str(SOURCE / '03_REPRODUCIBILITY'))
from label_case import title_case

PATCHES = {
    'ONET_2_A_1_e': ('Mathematics (O*NET Skill)', 'technical'),
    'ONET_2_B_3_e': ('Programming (O*NET Skill)', 'digital'),
    'DIGCOMP_3_4': ('Programming (DigComp Competence)', 'digital'),
}
ROLE_MAP = {'R01': 'M251201', 'R02': 'M252403', 'R06': 'M254302'}


def read(path):
    with path.open(newline='', encoding='utf-8-sig') as stream:
        return list(csv.DictReader(stream))


def write(name, rows, fields=None):
    path = ROOT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def sql_literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def norm(term):
    # Match the deployed backend's exact lookup normalization, not fuzzy identity.
    return term.strip().lower()


def resolve_aliases(taxonomy, aliases):
    canonical = defaultdict(set)
    all_terms = defaultdict(set)
    for row in taxonomy:
        canonical[norm(row['canonical_name'])].add(row['skill_id'])
        all_terms[norm(row['canonical_name'])].add(row['skill_id'])
    assert all(len(v) == 1 for v in canonical.values()), 'Canonical names still collide'
    for row in aliases:
        all_terms[norm(row['alias'])].add(row['skill_id'])
    kept, review = [], []
    for row in aliases:
        term = norm(row['alias'])
        canonical_owner = canonical.get(term, set())
        if len(all_terms[term]) == 1 or row['skill_id'] in canonical_owner:
            kept.append(row)
        else:
            review.append(dict(row, candidate_skill_ids='|'.join(sorted(all_terms[term])),
                               reason='Canonical Label Takes Priority' if canonical_owner
                               else 'Ambiguous Alias Requires Contextual Review'))
    after = defaultdict(set)
    for row in taxonomy:
        after[norm(row['canonical_name'])].add(row['skill_id'])
    for row in kept:
        after[norm(row['alias'])].add(row['skill_id'])
    assert all(len(v) == 1 for v in after.values())
    return kept, review


def main():
    tables = SOURCE / '01_TABLES'
    roles, skills, aliases, links, lineage = [read(tables / name) for name in (
        'D11_STEM_roles.csv', 'skill_taxonomy.csv', 'skill_aliases.csv',
        'role_skills.csv', 'role_skills_lineage.csv')]
    coverage = read(tables / 'D13_role_esco_coverage.csv')
    mapping_review = read(tables / 'D13_role_esco_mapping_review.csv')
    approved_role_ids = {r['role_id'] for r in coverage if r['mapping_confidence'].lower() in ('medium', 'high')}
    assert len(approved_role_ids) == 442
    mapping_by_id = {r['role_id']: r for r in coverage}
    legacy_skills = read(LEGACY / 'D6_skill_taxonomy.csv')
    legacy_aliases = read(LEGACY / 'D6_skill_aliases.csv')
    assert (len(roles), len(skills), len(links), len(aliases)) == (655, 6080, 41024, 37654)
    assert len(legacy_skills) == 41 and len(legacy_aliases) == 76
    by_pair = {(r['role_id'], r['skill_id']): r for r in lineage}
    core, conditional, core_lineage, conditional_lineage = [], [], [], []
    for row in links:
        evidence = by_pair[(row['role_id'], row['skill_id'])]
        relation = evidence['relation_type']
        assert relation in ('essential', 'optional')
        assert float(row['importance']) == (100 if relation == 'essential' else 50)
        (core if relation == 'essential' else conditional).append(row)
        (core_lineage if relation == 'essential' else conditional_lineage).append(evidence)
    assert (len(core), len(conditional)) == (18821, 22203)
    approved_core = [r for r in core if r['role_id'] in approved_role_ids]
    low_core = [r for r in core if r['role_id'] not in approved_role_ids]
    assert (len(approved_core), len(low_core)) == (13147, 5674)
    assert {r['role_id'] for r in approved_core} == approved_role_ids
    role_ids = {r['role_id'] for r in roles}
    skill_ids = {r['skill_id'] for r in skills}
    assert len(role_ids) == 655 and all(r['masco_code'].isdigit() and len(r['masco_code']) == 6 for r in roles)
    assert len({norm(r['role_title']) for r in roles}) == 655
    assert len({r['masco_code'] for r in roles}) == 655
    assert len({(r['role_id'], r['skill_id']) for r in links}) == len(links)
    assert {r['role_id'] for r in core} == role_ids
    assert all(r['skill_id'] in skill_ids for r in links)
    canonical_by_id = {s['skill_id']: s['canonical_name'] for s in skills}
    assert all(r['skill_name'] == canonical_by_id[r['skill_id']] for r in links)
    # Qualify different framework concepts; do NOT merge them by display label.
    from sentence_transformers import SentenceTransformer
    import numpy as np
    original = {r['skill_id']: r for r in legacy_skills}
    patches = []
    for sid, (label, category) in PATCHES.items():
        row = original[sid]
        assert label == title_case(label, protected={'O*NET': 'O*NET', 'DigComp': 'DigComp'})
        patches.append({'skill_id': sid, 'old_name': row['canonical_name'],
                        'old_definition': row['definition'], 'canonical_name': label,
                        'skill_type': category, 'embedding_text': label + '. ' + row['definition']})
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', local_files_only=True, device='cpu')
    vectors = model.encode([p['embedding_text'] for p in patches], normalize_embeddings=True,
                           show_progress_bar=False).astype(np.float32)
    assert vectors.shape == (3, 384) and np.isfinite(vectors).all()
    assert np.allclose(np.linalg.norm(vectors, axis=1), 1, atol=1e-5)
    for row, vector in zip(patches, vectors):
        row['embedding'] = '[' + ','.join(f'{float(x):.8f}' for x in vector) + ']'
    for row in legacy_skills:
        if row['skill_id'] in PATCHES:
            row['canonical_name'], row['skill_type'] = PATCHES[row['skill_id']]
            row['embedding_384'] = next(p['embedding'] for p in patches if p['skill_id'] == row['skill_id'])
    active_aliases, review_aliases = resolve_aliases(skills + legacy_skills, aliases + legacy_aliases)
    for r in coverage:
        approved = r['role_id'] in approved_role_ids
        r['review_status'] = 'auto_approved_medium_or_high_test_mapping' if approved else 'pending_low_confidence_review'
        r['use_in_role_skills'] = 'true' if approved else 'false'
        r['production_ready'] = 'false'
    for r in mapping_review:
        approved = r['role_id'] in approved_role_ids
        r['review_status'] = 'auto_approved_medium_or_high_test_mapping' if approved else 'pending_low_confidence_review'
        r['reviewer'] = 'User-Authorized Automated Confidence Rule' if approved else ''
        r['review_date'] = '2026-08-30' if approved else ''
        r['review_decision'] = 'Approved for Test Mapping' if approved else 'Pending Review'
        r['review_notes'] = ('User authorized automatic approval at Medium or High confidence. '
            'Mapping relationship retained; not an official crosswalk or exact occupational equivalence. '
            'Only ESCO essential links retained as test core candidates; optional skills remain conditional.'
            if approved else 'Below user-authorized Medium threshold. ESCO comparison retained; skill requirements held out.')
        r['production_ready'] = 'false'
    for r in core_lineage + conditional_lineage:
        r['mapping_review_status'] = mapping_by_id[r['role_id']]['review_status']
    write('01_TABLES/role_skills.csv', approved_core)
    write('01_TABLES/role_skills_low_confidence_review.csv', low_core)
    write('01_TABLES/role_skills_conditional.csv', conditional)
    write('01_TABLES/role_skills_lineage.csv', [r for r in core_lineage if r['role_id'] in approved_role_ids])
    write('01_TABLES/role_skills_low_confidence_lineage.csv', [r for r in core_lineage if r['role_id'] not in approved_role_ids])
    write('01_TABLES/role_skills_conditional_lineage.csv', conditional_lineage)
    write('01_TABLES/D13_role_esco_coverage.csv', coverage)
    write('01_TABLES/D13_role_esco_mapping_review.csv', mapping_review)
    metadata_rows = []
    for r in coverage:
        approved = r['role_id'] in approved_role_ids
        metadata_rows.append({'metadata_key': 'd13_quality_fix_20260830.mapping.' + r['role_id'],
            'metadata_value': json.dumps({'role_id': r['role_id'], 'masco_code': r['masco_code'],
                'esco_code': r['chosen_esco_code'], 'mapping_relation': r['mapping_relation'],
                'mapping_confidence': r['mapping_confidence'], 'review_status': r['review_status'],
                'use_in_role_skills': approved, 'approval_threshold': 'medium',
                'reviewer': 'User-Authorized Automated Confidence Rule' if approved else None,
                'review_date': '2026-08-30' if approved else None,
                'approval_is_not_exact_equivalence': True, 'production_ready': False}, separators=(',', ':'))})
    write('01_TABLES/dataset_metadata.csv', metadata_rows)
    write('01_TABLES/skill_aliases.csv', [r for r in active_aliases if r['skill_id'] in skill_ids])
    write('01_TABLES/legacy_skill_taxonomy_patch.csv', patches)
    write('02_QA/combined_active_skill_aliases.csv', active_aliases)
    write('02_QA/ambiguous_alias_review.csv', review_aliases)
    write('02_QA/legacy_skill_taxonomy_after.csv', legacy_skills)
    write('02_QA/legacy_role_merge_map.csv', [dict(old_role_id=k, canonical_role_id=v,
          basis='Original D1 Title and MASCO Unit Group; Original Row Archived') for k, v in ROLE_MAP.items()])
    for name in ('D11_STEM_roles.csv', 'skill_taxonomy.csv', 'skill_taxonomy_lineage.csv',
                 'ESCO_comparison_preservation.csv', 'MASCO2020_role_crosswalk.csv', 'D13_mapping_evidence.csv'):
        shutil.copyfile(tables / name, ROOT / '01_TABLES' / name)
        assert (tables / name).read_bytes() == (ROOT / '01_TABLES' / name).read_bytes()
    active_alias_pairs = {(r['skill_id'], r['alias']) for r in active_aliases}
    alias_lineage = read(tables / 'skill_aliases_lineage.csv')
    write('01_TABLES/skill_aliases_lineage.csv', [r for r in alias_lineage if (r['skill_id'], r['alias']) in active_alias_pairs])
    write('02_QA/held_alias_source_lineage.csv', [r for r in alias_lineage if (r['skill_id'], r['alias']) not in active_alias_pairs])
    def pair_hash(rows):
        payload = ''.join(r['role_id'] + '|' + r['skill_id'] + '|' + str(int(float(r['importance']))) + ';'
                          for r in sorted(rows, key=lambda r: (r['role_id'], r['skill_id'])))
        return hashlib.md5(payload.encode()).hexdigest()
    values = ',\n'.join('(' + ','.join(sql_literal(p[k]) for k in (
        'skill_id', 'old_name', 'old_definition', 'canonical_name', 'skill_type', 'embedding')) + ')'
        for p in patches)
    sql = (ROOT / 'migration.template.sql').read_text()
    mapping_values = ',\n'.join('(' + ','.join(sql_literal(r[k]) for k in (
        'role_id', 'chosen_esco_code', 'mapping_relation', 'mapping_confidence')) + ',' +
        ('true' if r['role_id'] in approved_role_ids else 'false') + ',' + sql_literal(r['review_status']) + ')'
        for r in coverage)
    for token, replacement in {'@@SKILL_PATCHES@@': values, '@@PAIR_HASH@@': pair_hash(links),
                                '@@MAPPING_APPROVALS@@': mapping_values,
                                '@@ALIAS_REMOVALS@@': str(len(review_aliases))}.items():
        sql = sql.replace(token, replacement)
    assert '@@' not in sql
    (ROOT / '03_DATABASE_DRAFT').mkdir(exist_ok=True)
    (ROOT / '03_DATABASE_DRAFT/DATA_QUALITY_FIX.sql').write_text(sql)
    core_counts, old_counts = Counter(r['role_id'] for r in core), Counter(r['role_id'] for r in links)
    digital = {r['role_id'] for r in core if r['skill_type'] == 'digital'}
    write('02_QA/role_requirement_audit.csv', [dict(role_id=r['role_id'], masco_code=r['masco_code'],
        role_title=r['role_title'], original_inventory=old_counts[r['role_id']], core_candidates=core_counts[r['role_id']],
        approved_core_candidates=core_counts[r['role_id']] if r['role_id'] in approved_role_ids else 0,
        conditional_skills=old_counts[r['role_id']] - core_counts[r['role_id']],
        empty_digital_band=r['role_id'] not in digital,
        mapping_confidence=mapping_by_id[r['role_id']]['mapping_confidence'],
        mapping_relation=mapping_by_id[r['role_id']]['mapping_relation'],
        mapping_approval=mapping_by_id[r['role_id']]['review_status'],
        status='User-Authorized Test Core Candidates; Not Exact MASCO-ESCO Equivalence'
        if r['role_id'] in approved_role_ids else 'Low Confidence; Requirements Held Out for Review') for r in roles])
    report = {'result': 'PASS_LOCAL_DATA_CHECKS', 'live_applied': False, 'source_roles': 655,
        'source_skill_concepts_preserved': 6080, 'source_role_skill_links': 41024,
        'all_source_essential_links': len(core), 'approved_core_candidate_links': len(approved_core),
        'low_confidence_essential_links_held': len(low_core), 'conditional_links': len(conditional),
        'auto_approved_roles_medium_and_high': len(approved_role_ids),
        'low_confidence_roles_pending': len(role_ids - approved_role_ids),
        'auto_approved_confidence_counts': dict(Counter(r['mapping_confidence'] for r in coverage if r['role_id'] in approved_role_ids)),
        'core_only_roles_without_digital_band': len(role_ids - digital),
        'approved_roles_without_digital_band': len(approved_role_ids - digital),
        'active_combined_alias_rows': len(active_aliases), 'archived_alias_rows': len(review_aliases),
        'remaining_exact_term_to_multiple_skill_id_conflicts': 0,
        'skill_ids_merged': 0, 'qualified_framework_concepts': 3,
        'role_merge_map': ROLE_MAP, 'unresolved_legacy_group_roles': ['R03','R04','R05','R07','R08','R09','R10'],
        'minimum_core_candidates': min(core_counts.values()), 'maximum_core_candidates': max(core_counts.values()),
        'teacher_before': old_counts['M232102'], 'teacher_after': core_counts['M232102'],
        'esco_comparisons_preserved': True, 'masco_roles_and_embeddings_unchanged': True,
        'live_sql_execution_tested': False, 'database_schema_changed': False,
        'backend_changed': False, 'release_scope': 'Dataset Only; Database Migration Draft Not Applied',
        'source_pair_md5': pair_hash(links), 'sql_sha256': hashlib.sha256(sql.encode()).hexdigest()}
    (ROOT / '02_QA/validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
