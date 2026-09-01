# D13 — complete D11 mapping, TEST release

Ready for testing. This release adds the remaining **562 mappings**, bringing the D11 scope to **657 six-digit MASCO roles**. It also corrects six previous assignments. ESCO codes and original D11 comparison values are retained; the original D11 files and earlier D13 release are unchanged.

## Results

| Output | Count |
|---|---:|
| MASCO roles with a primary ESCO assignment and skills | 657 |
| Close functional matches | 234 |
| Broader ESCO proxies | 197 |
| Partial ESCO proxies | 226 |
| Distinct ESCO occupations used | 382 |
| ESCO leaf skills | 6,164 |
| Skill aliases | 38,209 |
| Role–skill links | 40,948 |
| Embedding dimensions | 384 |

These are project-derived mappings for experiments, **not 657 exact equivalences** and not an official government crosswalk. Testing does not require completing the optional domain-review columns. Production flags deliberately remain false because this release is test-only. The data was appended to `rerouteher_test` on 2026-08-30; no production or model deployment was performed.

## Start here

- `01_TABLES/D13_role_esco_coverage.csv`: one primary ESCO code per MASCO role; confidence, relation, rationale, source links, previous codes and preserved ESCO comparisons.
- `01_TABLES/skill_taxonomy.csv`: `skill_id, canonical_name, definition, skill_type, embedding`.
- `01_TABLES/skill_aliases.csv`: official alternate/hidden labels and curated product/acronym aliases.
- `01_TABLES/role_skills.csv`: `role_id, skill_id, skill_name, skill_type, importance`.
- `01_TABLES/role_skills_lineage.csv`: selected ESCO occupation, official relation and mapping confidence for every link.
- `01_TABLES/D13_mapping_evidence.csv`: both MASCO and ESCO profiles, mapping rationale and sources.
- `01_TABLES/D13_mapping_candidates.csv`: eight retrieval candidates per role, for optional later refinement. Unselected candidates do not contribute skills. A curated primary choice can be outside the initial eight.
- `01_TABLES/D13_role_esco_mapping_review.csv`: optional future review worksheet; blank reviewer/decision fields do not block test use.
- `02_QA/D13_validation_report.json`: integrity-check results.
- `02_QA/D13_corrected_previous_mappings.csv`: six changed assignments, including Technical Sales Engineer, Data Architect, Character Rigger and Audit Assistant.
- `02_QA/D13_source_quality_issues.csv`: three issues retained transparently rather than silently editing D11.

For Excel/Sheets import, treat MASCO and ESCO codes as **text**, not numbers. The four-digit MASCO group is metadata only; `role_id = M` plus the six-digit MASCO code remains the role key.

## Append to your existing database — no structure changes

**Live `rerouteher_test` compatibility:** use `04_DATABASE/D13_APPEND_LIVE_COMPAT.sql` for the actual Coolify database. Its live CHECK constraints require `technical`, `soft` or `digital`; these checks were missing from the supplied ERD export. The original SQL below was rejected and fully rolled back. The compatibility variant preserves all original ESCO types, URIs, reuse levels and scheme memberships in `dataset_metadata` under `d13_test_20260830.skill_type.<skill_id>`. Digital/DigComp collection members use `digital`, non-knowledge transversal skills would use `soft`, and remaining skills use the coarse test bucket `technical`. This selected dataset contains 910 digital and 5,254 technical skills. This adapter is not an official category equivalence. Source CSVs are unchanged, and the variant refuses any database other than `rerouteher_test`.

The live-compatible import **committed successfully in 18 seconds** on 2026-08-30. It added 657 roles, 6,164 skills, 38,209 aliases, 40,948 role-skill links and 40,948 lineage rows. The existing 10 roles were unchanged, and normalized schema dumps before and after were identical. See `02_QA/D13_live_import_receipt.json` for the verified totals and checks.

For the same existing test schema, open `04_DATABASE/D13_APPEND_LIVE_COMPAT.sql` in **pgAdmin Query Tool** and execute the entire file. All data is embedded; no CSV imports or directory setup are required. Alternatively:

```sh
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f 04_DATABASE/D13_APPEND_LIVE_COMPAT.sql
```

The import targets your supplied **existing `rerouteher` schema**. It contains **no CREATE, ALTER, DROP, TRUNCATE or DELETE statements**, creates no extensions, and retains your existing `vector(384)` columns. The schema reference was read as data, not executed.

- Appends missing rows to `roles`, `skill_taxonomy`, `skill_aliases`, `role_skills`, `role_skill_lineage` and `dataset_metadata`, in dependency order.
- For an existing D11 role with the same role ID and six-digit MASCO code, updates **only `roles.esco_code`**. Its prior row is retained in `dataset_metadata` under `d13_test_20260830.before_role.<role_id>` before the update. Existing ratings, descriptions, embeddings and other role fields remain untouched.
- Keeps existing skill, alias and role-skill rows on key conflicts; **does not remove old skill links**. Re-running adds no duplicate primary keys. Existing incompatible role/skill identities cause the entire transaction to abort rather than overwrite them.
- Stores mapping confidence, rationale and ESCO comparison codes in your existing `dataset_metadata` table under `d13_test_20260830.mapping.<role_id>`; no extra columns or tables are needed.
- Uses one transaction. On error, changes roll back; in pgAdmin, run `ROLLBACK;` if the session remains in an aborted transaction. The original `D13_APPEND_EXISTING_SCHEMA.sql` is retained for provenance but is not suitable for these live CHECK constraints; use the compatible variant.

`.sql.gz` is the compressed form of the same SQL, not a pg_restore backup. Existing rows can reduce the number newly inserted; the input includes all 657 roles and all D13 links. This is an append/update test release, not a replacement of historical D1/D13 data. D11 fields that lack verified ISCO/O*NET mappings retain their original empty values rather than invented codes.

## Mapping and skill rules

1. Match D11 titles and descriptions/tasks to official ESCO v1.2.1 occupations, removing grade/competency wrappers for retrieval. Preferred/alternate labels, semantic candidates and curated duty-based corrections are used. Matching is not restricted to a shared four-digit group because MASCO and ESCO/ISCO numbering is not directly interchangeable.
2. Select one primary ESCO occupation per six-digit MASCO role. Preserve the original ESCO comparisons separately; do not union all candidate occupations' skills.
3. Join the chosen ESCO code to its official occupation URI, then `occupationSkillRelations_en.csv`, then `skills_en.csv`. Only linked leaf concepts are included. Official duplicate concept URIs are resolved by latest `modifiedDate`.
4. Set `importance=100` for ESCO essential relations and `50` for optional. This denotes the **ESCO proxy's** classification, not a verified Malaysian skill requirement.
5. Embed each canonical skill and definition (description fallback) with `sentence-transformers/all-MiniLM-L6-v2`, producing normalized 384-dimensional vectors. The NPY matrix, row index and CSV vectors agree.

High confidence is reserved for close matches to preferred labels. Close alternate/task matches and broader proxies are medium; partial proxies are low. Retrieval and lexical scores are not probabilities. The test can use all rows, or compare results after filtering `mapping_relation='close_match'`.

## Limits relevant to interpreting test results

- The 226 partial proxies are intentionally usable test approximations, not certified equivalents. Broader/partial profiles can miss specialty skills or include proxy-specific skills.
- Clinical specialties share the broader specialised-doctor occupation where ESCO lacks the specialty. Do not treat shared skill profiles as specialty-complete or infer Malaysian licensing rights.
- Halal, competent-person, public-service grade and other Malaysian requirements need local enrichment for future production use.
- Veterinary Manager has contradictory turf-related D11 task text; its mapping uses the veterinary title/description. Hygiene Technician and Communication Analyst also have flagged source-scope inconsistencies.
- No remote-work feasibility ratings are inferred or changed by this mapping.
- English/EU occupation and skill descriptions may not perfectly represent Malaysian practice. This test release is not fine-tuning, deployment, or recalibration of the existing matching model/MAI thresholds.
- No résumé dataset was introduced. JobHop v2 2019+ remains the only approved résumé source for any separate résumé work.

## Sources and reproducibility

Source CSV snapshots and hashes are included in `00_SOURCE_SNAPSHOT/` and `02_QA/D13_source_manifest.csv`. Official sources: [ESCO downloads](https://esco.ec.europa.eu/en/use-esco/download), [eMASCO](https://emasco.mohr.gov.my). Per-role eMASCO and ESCO links are recorded in the tables. The user-provided D13 brief supplies the task specification; the explicit user instruction replaces its D1 dependency with D11 and authorizes test-purpose mapping.

`03_REPRODUCIBILITY/` contains retrieval, mapping decisions, preparation, CSV authoring and validation/package scripts. Python requires NumPy and SentenceTransformers; the supplied run used sentence-transformers 5.7.0 and the locally cached MiniLM model. CSV authoring uses the bundled `@oai/artifact-tool` JS runtime. Re-running preparation reconstructs the excluded working JSON matrices from the included sources/candidates and the original sibling D11 directory; the candidate-retrieval script also references the preserved earlier D13 source snapshot. No live service is required when model weights are cached.
