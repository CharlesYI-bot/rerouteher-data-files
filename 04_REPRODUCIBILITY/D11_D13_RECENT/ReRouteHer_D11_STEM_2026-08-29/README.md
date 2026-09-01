# D11 — eMASCO STEM expansion of D1

This release corrects the D11 scope. D11 is not limited to the ten MASCO unit groups represented by the original D1 roles. It expands the D1 role-table structure to every occupation listed in the official eMASCO `STEM` category.

## Scope

- Official category: `STEM — Sains, Teknologi, Kejuruteraan dan Matematik`
- eMASCO definition: `Occupation that includes Science, Technology, Engineering or Mathematics element`
- Official directory: <https://emasco.mohr.gov.my/directory/category/stem>
- Occupations: 657 unique six-digit MASCO roles
- Tasks: 5,518 official task statements
- MASCO key: six digits without the display hyphen, for example `251201`
- MASCO display form: official `2512-01` form is retained in `masco_code_printed`
- Portal basis: MASCO 2020; the current eMASCO portal displays an enhancement notice

No resume dataset is used in D11. The JobHop v2 2019+ restriction applies to D12 and other resume-dependent work.

## Deliverables

- `00_SOURCE_SNAPSHOT/emasco_stem_occupations_2026-08-29.json` — official directory and role-detail snapshot with URLs and SHA-256 page hashes
- `01_TABLES/D11_STEM_roles.csv` — 657 roles; its first 24 columns exactly preserve the D1 schema
- `01_TABLES/D11_STEM_role_tasks.csv` — 5,518 task rows with source-level lineage
- `01_TABLES/D11_STEM_task_rating_lineage.csv` — transparent D1-method task pre-ratings and empty two-rater fields
- `01_TABLES/D11_STEM_role_rating_lineage.csv` — role-level pre-rating aggregation
- `01_TABLES/D11_STEM_D1_scope_lineage.csv` — relationship to the original ten D1 roles
- `01_TABLES/D11_STEM_source_manifest.csv` — source and comparison-data provenance
- `02_QA/D11_STEM_validation_checks.csv` — machine-readable validation gates
- `02_QA/D11_STEM_build_summary.json` — release counts and caveats
- Final workbook: `../outputs/01a047e7-ceba-7df3-8d1a-ba8071e66430/D11_STEM_D1_Structure.xlsx`

## Data rules

1. `masco_code` is always the six-digit role code, never the four-digit unit-group code.
2. The original D1 columns remain first and in their original order.
3. ESCO codes and titles remain comparison metadata. They are populated only where the existing project crosswalk contains an exact six-digit MASCO mapping; no missing ESCO values are guessed.
4. The official role page supplies the title, description, hierarchy, categories, and tasks whenever present.
5. Four exact role pages do not expose a task list: `3112-19`, `3118-07`, `3118-10`, and `3118-11`. Their task rows inherit the official four-digit unit-group task list and are marked `unit_group_inherited` with the unit-group source URL.
6. Remote/flexible and AI-exposure fields are reproducible keyword pre-ratings based on the D1 method. They are not production-approved until two independent human raters reconcile the task labels.

## Validation result

- 657 roles and 657 unique six-digit MASCO codes
- 5,518 task rows with complete source lineage
- 653 roles with exact occupation-level task pages
- 4 roles with transparent official unit-group task fallback
- 7 roles with an exact retained ESCO comparison in the current project crosswalk
- 26 STEM roles falling within one of the original ten D1 unit groups
- Six release QA checks pass
- Exported XLSX re-imports successfully with all eight sheets and zero summary formula errors

See `D12_IMPACT.md` before retraining or deploying the MASCO matcher.

## Reproduce

Run from the workspace root:

```bash
/Users/charlesyi/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 ReRouteHer_D11_STEM_2026-08-29/03_REPRODUCIBILITY/scrape_emasco_stem.py
rerouteher-esco-tfidf/.venv/bin/python ReRouteHer_D11_STEM_2026-08-29/03_REPRODUCIBILITY/build_d11_stem_tables.py
/Users/charlesyi/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node ReRouteHer_D11_STEM_2026-08-29/03_REPRODUCIBILITY/build_d11_stem_workbook.mjs
/Users/charlesyi/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node ReRouteHer_D11_STEM_2026-08-29/03_REPRODUCIBILITY/verify_d11_stem_workbook.mjs
```
