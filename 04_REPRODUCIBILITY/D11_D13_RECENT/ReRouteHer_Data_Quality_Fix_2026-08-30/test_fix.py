"""Independent regression tests for the corrected data artifact (no DB writes)."""
from collections import Counter
from pathlib import Path
import json
import sys
import unittest

from build_fix import ROOT, SOURCE, PATCHES, read, resolve_aliases


class DataQualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = read(SOURCE / '01_TABLES/role_skills.csv')
        cls.core = read(ROOT / '01_TABLES/role_skills.csv')
        cls.low = read(ROOT / '01_TABLES/role_skills_low_confidence_review.csv')
        cls.conditional = read(ROOT / '01_TABLES/role_skills_conditional.csv')

    def test_lossless_skill_inventory_partition(self):
        normalize = lambda rows: Counter(tuple(sorted(row.items())) for row in rows)
        self.assertEqual(normalize(self.original), normalize(self.core + self.low + self.conditional))
        self.assertEqual({row['importance'] for row in self.core}, {'100'})
        self.assertEqual({row['importance'] for row in self.conditional}, {'50'})

    def test_all_masco_roles_and_esco_comparisons_preserved_byte_for_byte(self):
        for name in ('D11_STEM_roles.csv', 'skill_taxonomy.csv', 'ESCO_comparison_preservation.csv'):
            self.assertEqual((ROOT / '01_TABLES' / name).read_bytes(), (SOURCE / '01_TABLES' / name).read_bytes())
        before = read(SOURCE / '01_TABLES/D13_role_esco_coverage.csv')
        after = read(ROOT / '01_TABLES/D13_role_esco_coverage.csv')
        for original, corrected in zip(before, after):
            for k in original:
                if k not in ('review_status', 'use_in_role_skills', 'production_ready'):
                    self.assertEqual(original[k], corrected[k])

    def test_shared_skills_keep_identical_ids_and_names(self):
        skills = {r['skill_id']: r['canonical_name'] for r in read(ROOT / '01_TABLES/skill_taxonomy.csv')}
        self.assertEqual(len(skills), 6080)
        for row in self.core + self.low + self.conditional:
            self.assertEqual(row['skill_name'], skills[row['skill_id']])

    def test_teacher_subject_specialisms_are_conditional_not_core(self):
        teacher_core = [r for r in self.core if r['role_id'] == 'M232102']
        teacher_conditional = [r for r in self.conditional if r['role_id'] == 'M232102']
        self.assertEqual((len(teacher_core), len(teacher_conditional)), (11, 104))
        aircraft = '2672f6a9-1e70-43c5-859d-e6a0fc9ea0f1'
        self.assertNotIn(aircraft, {r['skill_id'] for r in teacher_core})
        self.assertIn(aircraft, {r['skill_id'] for r in teacher_conditional})

    def test_all_approved_roles_have_core_candidates(self):
        self.assertEqual(len({r['role_id'] for r in self.core}), 442)
        self.assertEqual(len(self.core), 13147)
        self.assertEqual(min(Counter(r['role_id'] for r in self.core + self.low).values()), 6)

    def test_user_threshold_includes_medium_and_high_only(self):
        coverage = read(ROOT / '01_TABLES/D13_role_esco_coverage.csv')
        approved = {r['role_id'] for r in coverage if r['use_in_role_skills'] == 'true'}
        self.assertEqual(approved, {r['role_id'] for r in coverage if r['mapping_confidence'] in ('medium', 'high')})
        self.assertEqual({r['role_id'] for r in self.core}, approved)
        self.assertEqual(len({r['role_id'] for r in self.low}), 213)
        self.assertNotIn('M151108', approved)
        village = next(r for r in coverage if r['role_id'] == 'M151108')
        self.assertEqual(village['chosen_esco_code'], '1330.5')
        self.assertEqual(village['mapping_relation'], 'partial_proxy')
        self.assertEqual(village['review_status'], 'pending_low_confidence_review')

    def test_metadata_uses_existing_two_column_structure(self):
        metadata = read(ROOT / '01_TABLES/dataset_metadata.csv')
        self.assertEqual(len(metadata), 655)
        self.assertEqual(set(metadata[0]), {'metadata_key', 'metadata_value'})
        self.assertEqual(sum(json.loads(r['metadata_value'])['use_in_role_skills'] for r in metadata), 442)

    def test_unique_canonical_label_beats_wrong_alias(self):
        taxonomy = [{'skill_id':'a','canonical_name':'SQL'}, {'skill_id':'b','canonical_name':'Other'}]
        aliases = [{'skill_id':'a','alias':'sql'}, {'skill_id':'b','alias':' SQL '}]
        kept, review = resolve_aliases(taxonomy, aliases)
        self.assertEqual([r['skill_id'] for r in kept], ['a'])
        self.assertEqual([r['skill_id'] for r in review], ['b'])

    def test_unknown_ambiguous_alias_is_not_arbitrarily_assigned(self):
        taxonomy = [{'skill_id':'a','canonical_name':'A'}, {'skill_id':'b','canonical_name':'B'}]
        aliases = [{'skill_id':'a','alias':'shared'}, {'skill_id':'b','alias':'shared'}]
        kept, review = resolve_aliases(taxonomy, aliases)
        self.assertEqual(kept, [])
        self.assertEqual(len(review), 2)

    def test_combined_alias_dictionary_has_no_conflicting_id(self):
        taxonomy = read(ROOT / '01_TABLES/skill_taxonomy.csv') + read(ROOT / '02_QA/legacy_skill_taxonomy_after.csv')
        active = read(ROOT / '02_QA/combined_active_skill_aliases.csv')
        _, remaining = resolve_aliases(taxonomy, active)
        self.assertEqual(remaining, [])
        self.assertEqual(len(read(ROOT / '02_QA/ambiguous_alias_review.csv')), 446)

    def test_distinct_framework_concepts_are_not_falsely_merged(self):
        patch = read(ROOT / '01_TABLES/legacy_skill_taxonomy_patch.csv')
        self.assertEqual({r['skill_id'] for r in patch}, set(PATCHES))
        self.assertEqual(len({r['canonical_name'] for r in patch}), 3)
        for row in patch:
            self.assertEqual(len(json.loads(row['embedding'])), 384)

    def test_deployment_is_held_for_backend_scoring_bug(self):
        audit = read(ROOT / '02_QA/role_requirement_audit.csv')
        self.assertEqual(sum(r['empty_digital_band'] == 'True' for r in audit), 190)
        sql = (ROOT / '03_DATABASE_DRAFT/DATA_QUALITY_FIX.sql').read_text()
        self.assertIn('\\set fix_commit false', sql)
        self.assertIn('\\set backend_compatibility_confirmed false', sql)
        self.assertIn('ROLLBACK;', sql)
        self.assertNotIn('CASCADE', sql)
        self.assertNotIn('ALTER TABLE', sql)
        self.assertNotIn('DROP TABLE', sql)
        self.assertNotIn('TRUNCATE', sql)


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(DataQualityTests))
    (ROOT / '02_QA/regression_results.json').write_text(json.dumps({
        'status': 'PASS' if result.wasSuccessful() else 'FAIL',
        'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
        'database_contacted': False, 'backend_modified': False,
    }, indent=2) + '\n')
    sys.exit(0 if result.wasSuccessful() else 1)
