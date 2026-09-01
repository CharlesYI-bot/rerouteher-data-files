# D13 — rebuilt on MASCO 2020 STEM, with Title Case display labels

Prepared 30 August 2026. This is a new D13 test release using the approved **655-role MASCO 2020 STEM dataset**, not the previous 657-role current-portal taxonomy. Previous releases, the live database, database structure and deployed models are unchanged.

## Results

| Output | Rows |
|---|---:|
| Six-digit MASCO 2020 roles with a primary ESCO assignment | 655 |
| Distinct ESCO occupations used | 376 |
| Changed primary ESCO assignments versus the inherited 2020 release | 16 |
| Concrete linked ESCO skills | 6,080 |
| Lowercase matching aliases | 37,654 |
| Role–skill links | 41,024 |
| Essential links, importance 100 | 18,821 |
| Optional links, importance 50 | 22,203 |
| Preserved original ESCO comparison records | 657 |

The 655 mappings comprise 243 close functional matches, 199 broader proxies and 213 partial proxies. These are **project-derived test mappings, not an official crosswalk or 655 exact equivalences**. No mapping is marked production-ready or independently human-validated.

## Title Case rules — applied consistently

Human-readable ESCO occupation titles, skill canonical names, preferred/alternate display labels, comparison titles, candidate titles, matched labels and `role_skills.skill_name` use the same Title Case function.

- Capitalize the first/last word and principal words.
- Keep interior articles, conjunctions and common prepositions lowercase: for example, **Occupational Health and Safety Inspector** and **Tools for ICT Test Automation**.
- Preserve acronyms, initialisms and technical/product spellings: **SQL**, **ICT**, **JavaScript**, **MS Excel**, **ATC**, **IntelliJ IDEA**, **3D**, **pH** and **t-SNE**. Source uppercase abbreviations and internal mixed-case product names are preserved, not passed through a naive `.title()` conversion.
- Do not turn ordinary lowercase words into unrelated acronyms: **Visual Aids**, **Basic Care**, and **People Who Need It** remain ordinary words, while explicit **HIV and AIDS** retain their acronym forms.
- Preserve punctuation and wording; normalize repeated whitespace. Multiline/semicolon-separated display labels are treated as separate titles.

Deliberate exceptions:

- **Raw source snapshots and explicitly named raw-label fields remain byte/source-faithful.** `preferred_label_raw`, `raw_label`, and `raw_labels_json` are provenance, not display fields.
- **`skill_aliases.alias` is lowercase for matching**, following the brief's alias rule. `skill_aliases_lineage.alias_display_title` supplies a Title Case display version; raw aliases are retained in `raw_labels_json`.
- **Codes, IDs, URIs, source URLs, machine enums, skill types and mapping-status values are not recased.** Casing a URI can change its identity.
- **Definitions and descriptions retain sentence case**, exactly as sourced. MASCO occupation titles retain the approved 2020 source wording/case; this request changes ESCO display labels.

The package includes a cell-level label audit and **21 regression tests**, including acronym/product/ordinary-word edge cases. The same display names are used in taxonomy, link tables, coverage, evidence, comparison records, workbook and generated SQL. The main three D13 CSV schemas remain `skill_taxonomy(skill_id, canonical_name, definition, skill_type, embedding)`, `skill_aliases(skill_id, alias, alias_source)`, and `role_skills(role_id, skill_id, skill_name, skill_type, importance)`.

## What was actually rebuilt

1. Read the approved 655 MASCO 2020 role identities and their inherited D11 profiles. No 2020-excluded source role was added back to active scope.
2. Run fresh candidate retrieval using the **2020 titles**, with new title/profile query vectors. Only the unchanged ESCO-side vectors were cached, after verifying their complete occupation records and row order against the raw ESCO source. MASCO/ISCO four-digit numeric prefix agreement is recorded as metadata, not used to rank candidates.
3. Apply 65 explicit 2020-specific title/duty decisions, check preferred-title matches, and reject misleading alternate-label matches. Other previously curated proxies are retained transparently when no stronger unambiguous identity is established; their method is not labelled a new human review.
4. Resolve each selected ESCO code to its occupation URI, then rebuild the official essential/optional leaf-skill join. Candidate occupations do not contribute extra skills.
5. Rebuild canonical skills and normalized aliases. Preserve every official alternate/hidden matching alias, deduplicating per skill and removing aliases equal to the canonical matching key.
6. Regenerate normalized 384-dimensional skill embeddings using `sentence-transformers/all-MiniLM-L6-v2` on **Title Case canonical name + period + ESCO description**, with definition as the fallback. This is embedding inference, not model training or deployment.

Examples of corrected assignments include Budget Manager, Chief Data Officer, Chief Information Security Officer, Art Director, Chemical Plant Supervisor, and the radiography/gallery/museum roles. All 16 code changes are shown in `02_QA/D13_mapping_changes.csv` (which retains all 655 before/after comparisons).

Fresh exact aliases are not accepted blindly. For example, the source lists “neurologist” under Physicist, “engine driver” under Train Driver, and a digital “concept artist” label under Conceptual Artist. These conflict with the supplied clinical, stationary-engine or digital-art duties. Rejected alternatives and reasons are recorded in `D13_exact_alias_rejections.csv`.

## Skill categories and preserved comparisons

For consistency with the existing database, operational CSV/SQL skill types use the same coarse project buckets as the previous compatible import: **914 digital and 5,166 technical**. Digital means ESCO digital/DigComp collection membership; non-knowledge transversal skills would be soft; the remaining skills default to technical. No selected record meets the soft rule in this source subset. This is a **test compatibility rule, not an official ESCO category equivalence or a validated technical/soft classification**. Original ESCO skill types, reuse levels and scheme memberships remain in `skill_taxonomy_lineage.csv` and SQL metadata.

The new coverage table retains the preceding 2020 release's code beside the new chosen code. `ESCO_comparison_preservation.csv` retains all 657 original current-portal comparison records, including the 19 sources excluded from active 2020 scope. All their identifiers are unchanged; only human-readable ESCO titles are recased. Byte-faithful raw copies are in `00_SOURCE_SNAPSHOT`.

The first 24 D11 role columns retain their D1-compatible order. Only ESCO assignment/display fields are updated; MASCO codes/titles, tasks, remote-work and AI pre-ratings, and role vectors remain unchanged. The inherited current-portal task profiles are **not** newly validated 2020 task evidence.

## Start here

- `01_TABLES/D11_STEM_roles.csv`: the same 655 MASCO 2020 roles, now with refreshed D13 ESCO assignments and display titles.
- `01_TABLES/D13_role_esco_coverage.csv`: primary mapping, relation/confidence, fresh title evidence, previous code and source links.
- `01_TABLES/skill_taxonomy.csv`, `skill_aliases.csv`, `role_skills.csv`: the core D13 outputs.
- `01_TABLES/skill_taxonomy_lineage.csv`, `skill_aliases_lineage.csv`, `role_skills_lineage.csv`: raw labels/types, display labels, embedding input and official relation provenance.
- Other tables: fresh candidate/evidence records, optional domain-review fields, the original MASCO-version crosswalk and preserved ESCO comparisons.
- `02_QA/D13_title_case_audit.csv`: raw-to-display label audit. Lowercase raw labels are intentional here.
- `02_QA/D13_validation_report.json`: independent structural, source-join, case, vector and artifact checks.
- `05_MODEL_ARTIFACTS`: skill vectors/index, embedding metadata, and unchanged D11 role vectors/index.
- `06_REVIEW/D13_MASCO2020_TitleCase_Review.xlsx` inside the ZIP: summary, all mappings/skills/aliases, changed mappings, case tests and ESCO comparison.
- `04_DATABASE`: optional self-contained SQL for a **separate empty test database**. Read its README before use.

CSV codes and UUIDs must be imported as text. Empty optional CSV fields mean missing/null, not zero. Do not use Excel's PROPER function on the labels: it corrupts protected spellings such as SQL and JavaScript.

## Database and runtime boundaries

No SQL has been executed. The generated import leaves the schema unchanged and refuses the existing `rerouteher_test`; it requires a separate empty `rerouteher_masco2020_test` with the existing schema already initialized. It also refuses nonempty target tables. This prevents both MASCO-version code collisions and silent retention of stale names/links through `ON CONFLICT DO NOTHING`.

This release does not migrate or replace a previously populated test database. Such a migration needs separate approval and reference-aware handling. No matcher threshold was retuned, no service deployed, and no résumé dataset introduced; JobHop v2 2019+ remains the approved scope for separate résumé work.

## Sources and reproducibility

The raw ESCO classification **v1.2.1** snapshots (`occupations_en.csv`, `skills_en.csv`, `occupationSkillRelations_en.csv`) are included unchanged. They are the leaf-skill source, not the occupation-by-skill-group matrix.

- ESCO: https://esco.ec.europa.eu/en/use-esco/download
- MASCO 2020 publication underlying the approved role release: https://www.dosm.gov.my/uploads/content-downloads/file_20220920110308.pdf
- Current STEM selection underlying that release: https://emasco.mohr.gov.my/directory/category/stem

Source hashes and per-record URLs are recorded. The D13 brief is archived as specification context; explicit user instructions replace its 10-role D1 dependency with the approved 655-role MASCO 2020 STEM dataset and require Title Case displays and an unchanged database schema.

Run the scripts in `03_REPRODUCIBILITY` in order: `retrieve_2020.py`, `prepare_d13_2020.py`, `author_d13.mjs`, `build_test_import.py`, `validate_d13.py`, `package_release.py`. They use the sibling original D13 and approved MASCO 2020 releases, including the previous guarded import generator, plus the cached MiniLM model. Python needs NumPy/SentenceTransformers; spreadsheet authoring uses the configured `@oai/artifact-tool` runtime. Raw retrieval caches, intermediate matrices, dependency links and preview images are omitted from the final ZIP but can be regenerated.
