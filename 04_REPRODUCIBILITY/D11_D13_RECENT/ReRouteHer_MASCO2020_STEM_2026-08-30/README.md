# ReRouteHer — MASCO 2020 STEM test dataset

Prepared 30 August 2026. This is a separate revision of D11 and D13. Previous releases, the live database, and the deployed matching model have not been changed.

## Result

| Scope | Rows |
|---|---:|
| Current eMASCO STEM source occupations | 657 |
| Source occupations retained with a reviewed 2020 counterpart | 638 |
| Source occupations excluded from the active release | 19 |
| Additional rows from splitting 15 combined source occupations | 18 |
| Duplicate 2020 target rows merged | 1 |
| **Final unique six-digit MASCO 2020 roles** | **655** |
| Referenced ESCO skills | 6,051 |
| Skill aliases | 37,521 |
| Role–skill links | 41,286 |
| Inherited D11 task records | 5,512 |

The role reconciliation is **638 + 18 − 1 = 655**, not simply 657 minus exclusions. No unrelated roles were added to the current STEM selection. Splits represent named components/grades or reviewed functions of retained source occupations.

## What “MASCO 2020” means here

Every active `masco_code` is a **six-digit occupation code**, not a four-digit unit-group code. The code and occupation title match the official 2020 English systematic index. Parent-group fields were updated to the 2020 hierarchy. `role_id` is `M` followed by that six-digit code.

Occupation identity was checked before accepting a code. A current code can exist in the 2020 index but refer to a different occupation. For example, current Audit and Risk Management Manager `121102` maps to 2020 `121106`; 2020 `121102` denotes Finance Manager.

The scope remains the **current official eMASCO STEM category**, translated to reviewed 2020 occupation identities. This release does **not** claim that MASCO 2020 published the same historical STEM-category designation. The input is a 29 August 2026 portal snapshot; the enhanced portal's edition is not independently asserted to be “2025.”

Official sources:

- MASCO 2020 English publication: https://www.dosm.gov.my/uploads/content-downloads/file_20220920110308.pdf — systematic occupation index, physical PDF pages 316–445; per-role physical pages are in the crosswalk.
- Current STEM scope: https://emasco.mohr.gov.my/directory/category/stem
- JPA SSPA Annex B grade-family reference: https://docs.jpa.gov.my/docs/sspa/SSPA_LAMPIRAN_B.pdf — used to revert current public-service grades to entries actually printed in MASCO 2020. This is not an official MASCO occupation crosswalk.

The source publication reports 6,630 occupation titles; the existing audited English index extraction contains 6,620 distinct observable codes. No missing codes were invented. Exclusion therefore means that a suitable identity was not established in the reviewed source, not proof that a profession did not exist.

## Mapping and exclusions

The 657 original records were resolved as follows:

| Method | Source records |
|---|---:|
| Exact normalized occupation title | 458 |
| Reviewed public-service grade reversion | 99 |
| Same-identity title variant | 33 |
| Reviewed functional counterpart | 32 |
| Combined title/grade split | 15 |
| Duplicate 2020 title — project canonical choice | 1 |
| No verified 2020 equivalent | 14 |
| Broad aggregate without one established 2020 identity | 4 |
| Corresponding grade entry unavailable in 2020 | 1 |

`MASCO2020_role_crosswalk.csv` records every decision, its reason, confidence, source title/code, target title/code, source URLs and primary-profile choice. These are **project-reviewed mappings, not an official cross-version crosswalk**. Fuzzy retrieval scores were used to find candidates, not as automatic acceptance criteria.

`MASCO2020_excluded_roles.csv` contains the 19 exclusions. They are archived, not erased from the source snapshot or ESCO comparison audit. The grade exclusion is Assistant Town/Urban and Rural Planning Officer JA7: JPA maps JA7 to JA38, while the reviewed 2020 entry is JA29; these were not silently treated as equivalent.

When several current records map to one target, one profile is used, preferring an exact title. Current Mechatronics Technician and Mechatronics Engineering Assistant converge on `311524`; the exact-title technician profile is primary. Both source decisions remain in the crosswalk. For duplicate printed Production Engineering Technician entries, `311910` is the project canonical target and `311915` is retained as an alternate in the audit.

## D11, remote work and D13 / ESCO

The first 24 D11 role columns remain in their original D1-compatible order. Additional columns distinguish current-source identity, MASCO version, evidence URLs, remap method and inherited-profile status.

Only the taxonomy identity is converted to 2020. **Task descriptions, remote-work and AI pre-ratings are inherited current D11 test profiles**, not newly extracted 2020 tasks or newly validated ratings. This is particularly important for split and functional-counterpart mappings. Original D11 source-quality warnings are propagated; three original warning rows become four after a warned source is split.

All 655 active roles keep their primary source's ESCO assignment. `ESCO_comparison_preservation.csv` also preserves the original D11/D13 ESCO comparison fields for **all 657 sources, including exclusions**. No ESCO code has been removed from that comparison audit.

Functional matches, split profiles and the canonical duplicate choice are marked `inherited_test_proxy` in D13. The prior mapping relation/confidence is separately preserved. Existing candidate/retrieval scores still describe the original current-role query, not a recomputed MASCO 2020 title match. Four-digit prefix comparison fields were recomputed, but numeric prefix agreement is not evidence of an official crosswalk. `production_ready` remains false.

Linked skills, aliases, lineage and skill vectors were filtered to the active role set. Every surviving role–skill importance value is unchanged from its primary source. Splits can increase the number of role–skill links even when the source-role selection shrinks.

## Files

- `01_TABLES/D11_STEM_roles.csv`: primary 655-role D1-compatible dataset.
- `01_TABLES/MASCO2020_retained_roles.csv`: compact active role list.
- `01_TABLES/MASCO2020_role_crosswalk.csv`: 675 source-to-target/exclusion audit rows.
- `01_TABLES/MASCO2020_excluded_roles.csv`: 19 excluded source records and reasons.
- `01_TABLES/ESCO_comparison_preservation.csv`: all 657 original comparison records.
- Other `01_TABLES` files: refreshed D11 task/rating lineage and D13 coverage, candidate, skill, alias and link tables.
- `02_QA`: validation results, remap decisions, original quality flags and 209 potential code/title collisions against the prior current-portal release.
- `05_MODEL_ARTIFACTS`: normalized 384-dimensional role/skill vectors and matching row indexes.
- `06_REVIEW/MASCO2020_STEM_Review.xlsx` inside the ZIP: readable summary, retained roles, exclusions, crosswalk and ESCO comparison.
- `04_DATABASE`: a guarded import for a **separate empty test schema**, not a migration of the existing database. Read its README before use.
- `00_SOURCE_SNAPSHOT`: unchanged current role snapshot, 2020 index extraction, user-supplied schema and source checksums. The official PDF is linked and hashed, not redistributed.

Role embeddings were recomputed using the already available `sentence-transformers/all-MiniLM-L6-v2` model on the 2020 title plus inherited task summary. The model was not trained or deployed. Skill embeddings are an exact unchanged row subset of the original D13 vectors. This conversion does not introduce any resume dataset or change the JobHop v2 2019+ training scope.

## Validation and limitations

`02_QA/validation_report.json` records 43 passing automated checks: exact 2020 code/title membership and cited-page presence, six-digit uniqueness, source reconciliation, ESCO preservation, foreign keys, source-equal links/tasks, embedding shapes/indexes/values, unchanged input hashes, spreadsheet totals and SQL structure. Every authored CSV cell was round-trip checked through the spreadsheet builder. The review workbook was visually inspected.

These checks prove structural consistency and documented source membership; they do not replace expert validation of functional equivalence, remote feasibility or licensing/qualification requirements. The 19 exclusions are conservative decisions with reasons. This remains a **test-only release**.

## Reproducibility

Scripts in `03_REPRODUCIBILITY` read the original sibling D11/D13 releases and MASCO 2020 PDF/index. They do not modify those sources. `mapping_decisions.py` contains the 199 explicitly reviewed non-unique-exact cases. `review_masco2020.py` prepares retrieval candidates; `extract_pdf_evidence.py` supplies a local text cache; `prepare_release.py` prepares data matrices and embeddings; `author_release.mjs` authors CSVs and the workbook; `build_test_import.py` builds the optional SQL; `validate_release.py` checks the release; `package_release.py` creates the archive.

Python requires NumPy, pypdf and the locally cached sentence-transformers model. Workbook authoring requires `@oai/artifact-tool` from the configured workspace runtime. Scripts resolve source directories relative to this release, except documented runtime/model dependencies. Large local intermediate JSON matrices, full PDF text caches, dependency symlinks and preview images are intentionally omitted from the deliverable ZIP; they can be regenerated from the sources.
