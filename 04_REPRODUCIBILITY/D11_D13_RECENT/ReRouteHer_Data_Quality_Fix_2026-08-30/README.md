# D13 MASCO 2020 — Dataset Quality Correction

Status: **dataset prepared and locally validated; live database data and backend unchanged.**

This release follows the user's instruction to auto-approve **Medium and High** confidence MASCO–ESCO mappings, while keeping the existing database structure. Approval is an explicit test-dataset acceptance rule, not a claim of exact occupational equivalence, official crosswalk authority, human review, or production readiness.

## What changed

| Item | Corrected dataset |
|---|---:|
| MASCO 2020 STEM roles retained | 655 |
| High-confidence mappings auto-approved | 117 |
| Medium-confidence mappings auto-approved | 325 |
| Low-confidence mappings held for review | 213 |
| Essential skill links for the 442 approved roles | 13,147 |
| Essential skill links held with low-confidence mappings | 5,674 |
| Optional/conditional skill links kept separately | 22,203 |
| ESCO skill concept IDs preserved | 6,080 |
| Ambiguous/conflicting alias rows held out, combined D1+D13 | 446 |

All 41,024 original role–skill links remain recoverable in the three disjoint tables. No role was discarded to force ESCO uniqueness. Role titles and six-digit MASCO codes are unique in the 655-role catalog. The same ESCO skill concept uses the same skill ID across all roles. ESCO comparisons, relationship types and original confidence labels are retained.

The spreadsheet audit kept source tables immutable, separated display labels from matching aliases, and checked identifiers and cross-table references. Existing ESCO Title Case labels, acronyms and product spelling are preserved.

## Main files

- `01_TABLES/D11_STEM_roles.csv`: all 655 roles, unchanged from the MASCO 2020 release, including original role embeddings and ESCO comparison fields.
- `01_TABLES/D13_role_esco_coverage.csv`: updated approval/use status using the user's Medium-or-High threshold. Codes, titles, mapping relationship and confidence are unchanged.
- `01_TABLES/D13_role_esco_mapping_review.csv`: recorded automated decisions, reviewer method, date and scope. Low-confidence entries remain pending.
- `01_TABLES/dataset_metadata.csv`: the same decisions encoded for the existing two-column metadata table (`metadata_key, metadata_value`); no database column additions are required.
- `01_TABLES/role_skills.csv`: **13,147 essential/core candidates for approved test mappings**. Same five-column format: `role_id, skill_id, skill_name, skill_type, importance`.
- `01_TABLES/role_skills_low_confidence_review.csv`: 5,674 essential links held out because their MASCO–ESCO mapping is Low confidence.
- `01_TABLES/role_skills_conditional.csv`: 22,203 optional specialisms. These are not universal deficiencies; links associated with Low-confidence mappings also remain subject to that mapping review.
- Corresponding `*_lineage.csv` files preserve the source relationship, IDs, URLs, confidence and updated mapping-review status.
- `01_TABLES/skill_taxonomy.csv`: the unchanged canonical 6,080-concept ESCO catalog and vectors.
- `01_TABLES/skill_aliases.csv`: cleaned D13 aliases. Raw held aliases and their source evidence are retained in `02_QA`.
- `01_TABLES/ESCO_comparison_preservation.csv`: unchanged comparison/history record, including historical role identities. It is not the active role catalog.
- `02_QA/role_requirement_audit.csv`: per-role counts, approval state, mapping relationship and empty-digital-band flags.
- `02_QA/validation.json` and `test_fix.py`: machine-readable validation and regression tests.

Do not concatenate the three role–skill partitions back into a universal readiness denominator. Do not load all files in this folder blindly: `01_TABLES` contains the D13 dataset and explicit review/reference partitions; `02_QA` contains audits and legacy-integration proposals, not additional production tables.

## Two observed examples

**Teacher, Vocational (`M232102`)** has a Medium-confidence close match, so it is approved by the requested rule. Its 115-skill inventory becomes **11 core candidates plus 104 conditional skills**. Aircraft Flight Control Systems and other alternative subject specialisms remain in the conditional file, not universal requirements.

**Village Community Center Manager (`M151108`)** retains its six-digit MASCO identity and the ESCO `1330.5` comparison. That comparison remains a **Low-confidence partial proxy**, so it is not auto-approved and contributes no rows to the approved core table. Keeping the comparison does not say that a community-center manager is identical to an ICT Operations Manager.

## Duplicate and legacy integration handling

The D13 role catalog has no duplicate normalized role titles or MASCO codes, and no duplicate role–skill pairs. Shared ESCO occupation codes are valid many-to-one comparison links, not duplicate MASCO identities. They must not be made unique by deleting valid roles.

`02_QA/legacy_role_merge_map.csv` proposes `R01 → M251201`, `R02 → M252403`, and `R06 → M254302` for a later database cleanup. The live R01 currently has title `duplicate`, MASCO `0`, ESCO `0`, and no active skill links; the proposal uses its original D1 Software Developer identity and archives the current row rather than silently restoring old data. The live dependency audit found 109 training examples linked to these three legacy roles, plus other historical records; a merge must preserve and reparent those records. **No live merge has been executed.**

Three legacy display labels are qualified in `legacy_skill_taxonomy_patch.csv`: Mathematics (O*NET Skill), Programming (O*NET Skill), and Programming (DigComp Competence). Applied mathematics is not automatically the same concept as ESCO mathematics knowledge. Programming skill, broad DigComp competence and programming knowledge are not silently merged either. Their original IDs and definitions remain intact; the three display-label embeddings were regenerated. O*NET Programming is assigned to the project's digital bucket rather than soft. ESCO display labels are unchanged.

For aliases, a unique canonical label takes priority over a conflicting alias. Where no canonical label disambiguates a shared alias, all competing alias rows are held for contextual review. The resulting **combined** exact-term dictionary has zero term-to-multiple-ID conflicts. This does not eliminate semantic ambiguity or missing-ID issues elsewhere.

Seven other legacy D1 group-level roles (`R03`, `R04`, `R05`, `R07`, `R08`, `R09`, `R10`) remain outside this 655-role STEM dataset. They need separate six-digit identity review; no codes have been invented for composite titles.

## Evidence and limits

The partition follows ESCO's distinction between [essential and optional occupational skills](https://esco.ec.europa.eu/en/about-esco/escopedia/escopedia/two-pillar-structure-esco). Essential is defined relative to the **ESCO occupation**; it does not prove that every inherited skill is mandatory for a mapped MASCO role. In particular, the user-approved Medium-confidence set includes broader proxies, whose relationship labels remain visible. These are approved **test core candidates**, not a calibrated assessment specification.

The local source is `ReRouteHer_D13_MASCO2020_2026-08-30`, including its ESCO v1.2.1 snapshot and MASCO source links. MASCO 2020 identities were retained without recoding. The inherited current eMASCO task profiles are not relabelled as historical 2020 task evidence. No resume dataset was used or model retrained in this correction.

The inherited digital/technical compatibility buckets are not a validated soft/digital/AI-readiness taxonomy. Five source DigComp concepts have blank official skill-type/reuse fields and broad labels; they are preserved as source concepts rather than falsely declared atomic skills. No complete leaf-only hierarchy validation is claimed. Review this taxonomy before production scoring.

## Database status — structure untouched

No live rows, columns, constraints, indexes, models or backend code were changed. A fresh approximately 39 MB database backup was created in the PostgreSQL persistent directory and its archive listing was checked; no full restore rehearsal has been run.

`03_DATABASE_DRAFT/DATA_QUALITY_FIX.sql` is a **draft, not executed or PostgreSQL-rehearsed**. It uses the existing tables, metadata archives, transactional guards and temporary work tables only; it does not change the permanent schema. It defaults to ROLLBACK, checks the exact inspected baseline, preserves historical references and comparisons, and requires a backup plus an explicit compatibility gate for commit. A fresh deletion confirmation is still required before live cleanup through Coolify.

Live activation is deferred in accordance with the user's dataset-first instruction. The deployed scorer gives free credit to empty digital bands; **128 of the 442 approved roles** have such a band after this cleanup (190 across all 655 original essential-only sets). Shared-ESCO first-row lookup, weak recommendation filling and cached/missing skill IDs also remain backend issues. Dataset preparation does not claim to have fixed those application behaviours.

## Rebuild and verify

Run `build_fix.py` with the bundled Python, the existing source release next to this directory, the locally cached `sentence-transformers/all-MiniLM-L6-v2` model, and the available `sentence_transformers`/NumPy dependencies. Run `test_fix.py` with Python to independently check the generated files. The tests do not contact PostgreSQL or modify the live app.
