"""Reconcile live outputs with the applied data-only release; read-only fixtures."""
import csv
import json
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent
DATA = PROJECT / 'ReRouteHer_Data_Quality_Fix_2026-08-30'
LEGACY = PROJECT / 'ReRouteHer_DataTeam_Fresh_HighStandard_2026-08-27/01_REFERENCE_TABLES'

def read(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def norm(s):
    return ' '.join(s.casefold().split())

def fixtures():
    retired = {'R01', 'R02', 'R06'}
    roles = read(DATA/'01_TABLES/D11_STEM_roles.csv') + [r for r in read(LEGACY/'D1_roles.csv') if r['role_id'] not in retired]
    taxonomy = {s['skill_id']:s for s in read(DATA/'01_TABLES/skill_taxonomy.csv') + read(DATA/'02_QA/legacy_skill_taxonomy_after.csv')}
    links = read(DATA/'01_TABLES/role_skills.csv') + [r for r in read(LEGACY/'D2_D5_role_skills.csv') if r['role_id'] not in retired]
    by_role = defaultdict(list)
    for link in links:
        link = dict(link)
        link['skill_name'] = taxonomy[link['skill_id']]['canonical_name']
        link['skill_type'] = taxonomy[link['skill_id']]['skill_type']
        by_role[link['role_id']].append(link)
    coverage = {r['role_id']:r for r in read(DATA/'01_TABLES/D13_role_esco_coverage.csv')}
    return {r['role_title']:r for r in roles}, taxonomy, by_role, coverage

def score(role, links, ids):
    weight = {'low':.2, 'medium':.4, 'high':.6}.get(role['ai_exposure'],.4)
    values = []
    for band in (('technical','soft'),('digital',)):
        members = [s for s in links if s['skill_type'] in band]
        total = sum(float(s['importance']) for s in members)
        matched = sum(float(s['importance']) for s in members if s['skill_id'] in ids)
        values.append(matched/total if total else 1)
    return round(((1-weight)*values[0] + weight*values[1])*100,1)

def main():
    raw = json.loads((ROOT/'live_results.json').read_text())
    roles, taxonomy, links, coverage = fixtures()
    audit = {'cases':[], 'gaps':[], 'fixture_basis':'Applied data-quality release plus seven retained legacy roles; no new database query or mutation.'}
    for c in raw['cases']:
        snap = c['snapshot']
        skills = snap['professional_skills']
        ids = {s.get('skill_id') for s in skills if s.get('skill_id')}
        titles = [r['role'] for r in snap['recommended_roles']]
        a = dict(case_id=c['case_id'], extracted_skills=len(skills), parsed_experiences=c['parsed']['experience_count'],
                 previous=snap['previous_occupation'],
                 missing_skill_ids=sum(not s.get('skill_id') for s in skills),
                 unknown_skill_ids=[s['skill_id'] for s in skills if s.get('skill_id') not in taxonomy],
                 duplicate_skill_ids=len(skills)-len(ids),
                 duplicate_skill_labels=len(skills)-len({norm(s['skill']) for s in skills}),
                 canonical_label_mismatches=[s for s in skills if s.get('skill_id') in taxonomy and s['skill'] != taxonomy[s['skill_id']]['canonical_name']],
                 duplicate_recommended_titles=len(titles)-len({norm(t) for t in titles}),
                 unknown_role_titles=[t for t in titles if t not in roles])
        audit['cases'].append(a)
        for rank,g in enumerate(c['gaps'],1):
            role = roles[g['target_role']]
            reqs = links[role['role_id']]
            mapping = coverage.get(role['role_id'],{})
            actual = g['result']
            expected_matches = {s['skill_name'] for s in reqs if s['skill_id'] in ids}
            digital = [s for s in reqs if s['skill_type']=='digital']
            audit['gaps'].append(dict(case_id=c['case_id'],rank=rank,role=g['target_role'],
                role_id=role['role_id'],masco_code=role['masco_code'],esco_code=role['esco_code'],
                mapping_confidence=mapping.get('mapping_confidence','legacy'),
                mapping_relation=mapping.get('mapping_relation','legacy'),
                mapping_approved=mapping.get('use_in_role_skills','legacy'),
                requirements=len(reqs),digital_requirements=len(digital),role_requirements=len(reqs)-len(digital),
                readiness=actual['readiness'],matched=len(actual['skills_have']),gaps_returned=len(actual['gaps']),
                ui_implied_total=len(actual['skills_have'])+len(actual['gaps']),
                score_reconciles=score(role,reqs,ids)==actual['readiness'],
                matches_reconcile=expected_matches==set(actual['skills_have']),
                empty_profile_baseline=score(role,reqs,set()),
                six_digit=bool(re.fullmatch(r'\d{6}',role['masco_code']))))
    gs=audit['gaps']; cs=audit['cases']
    all_http=[c['parse_http'] for c in raw['cases']]+[c['snapshot_http'] for c in raw['cases']]+[g['http'] for c in raw['cases'] for g in c['gaps']]
    audit['summary'] = dict(resumes=len(cs),gap_checks=len(gs),request_status_counts=dict(Counter(str(h['status']) for h in all_http)),
        scores_100=sum(g['readiness']==100 for g in gs),scores_0=sum(g['readiness']==0 for g in gs),
        scores_0_to_3=sum(g['readiness']<=3 for g in gs),
        missing_requirement_scores_100=sum(g['readiness']==100 and g['requirements']==0 for g in gs),
        cases_with_false_100=len({g['case_id'] for g in gs if g['readiness']==100 and g['requirements']==0}),
        first_recommendation_false_100=sum(g['rank']==1 and g['readiness']==100 and g['requirements']==0 for g in gs),
        unique_unscorable_roles=len({g['role_id'] for g in gs if not g['requirements']}),
        nonempty_zero_match_positive_scores=[g for g in gs if g['requirements'] and not g['matched'] and g['readiness']>0],
        lower_than_065_matches=sum(c['previous']['confidence']<.65 for c in cs),
        no_experience_cases=[c['case_id'] for c in cs if c['parsed_experiences']==0],
        duplicate_skill_ids=sum(c['duplicate_skill_ids'] for c in cs),
        duplicate_skill_labels=sum(c['duplicate_skill_labels'] for c in cs),
        duplicate_recommendations=sum(c['duplicate_recommended_titles'] for c in cs),
        missing_skill_ids=sum(c['missing_skill_ids'] for c in cs),
        unknown_skill_ids=sum(len(c['unknown_skill_ids']) for c in cs),
        canonical_label_mismatches=sum(len(c['canonical_label_mismatches']) for c in cs),
        score_mismatches=[g for g in gs if not g['score_reconciles']],
        matched_skill_mismatches=[g for g in gs if not g['matches_reconcile']],
        incorrect_ui_denominator=sum(g['requirements']!=g['ui_implied_total'] for g in gs),
        six_digit_recommendations=sum(g['six_digit'] for g in gs),
        legacy_recommendations=[g for g in gs if not g['six_digit']],
        api_returns_masco_code=any('masco_code' in r for c in raw['cases'] for r in c['snapshot']['recommended_roles']),
        api_returns_role_id=any('role_id' in r for c in raw['cases'] for r in c['snapshot']['recommended_roles']),
        total_extracted_skills=sum(c['extracted_skills'] for c in cs),
        median_parse_seconds=round(statistics.median(c['parse_http']['seconds'] for c in raw['cases']),3),
        max_parse_seconds=max(c['parse_http']['seconds'] for c in raw['cases']),
        median_snapshot_seconds=round(statistics.median(c['snapshot_http']['seconds'] for c in raw['cases']),3),
        median_gap_seconds=round(statistics.median(g['http']['seconds'] for c in raw['cases'] for g in c['gaps']),3))
    (ROOT/'audit_results.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps(audit['summary'],indent=2))

if __name__=='__main__': main()
