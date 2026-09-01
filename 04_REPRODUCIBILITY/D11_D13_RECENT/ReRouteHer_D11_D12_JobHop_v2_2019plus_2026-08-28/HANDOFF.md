# D11–D12 file map and rerun guide

## Review first

1. Confirm the ten curated six-digit anchors in
   `01_D11_REFERENCE_TABLES/D11_curated_role_anchor_map.csv`.
2. Review the project crosswalk and sparsity actions in
   `02_D12_MODEL/D12_esco_to_masco_label_crosswalk.csv`.
3. Review held-out results and blockers in `02_D12_MODEL/D12_metrics.json`.
4. Run child-specific two-rater remote/AI review before production use.

## Rebuild

Run from the workspace root with Python 3.12 and the local dependencies already
used by the high-standard release:

```bash
python3 ReRouteHer_D11_D12_JobHop_v2_2019plus_2026-08-28/04_REPRODUCIBILITY/build_d11_d12.py
python3 ReRouteHer_D11_D12_JobHop_v2_2019plus_2026-08-28/04_REPRODUCIBILITY/validate_d11_d12.py
```

The build reads the existing approved JobHop, MASCO, ESCO, and D1 reference
files by relative workspace path. It does not fetch data or use another resume
dataset.

## Database

Apply `03_DATABASE/D11_roles_six_digit_migration.sql` only after backing up the
current database and confirming the anchor map. The migration is transactional
and includes a hard six-digit assertion.

## Model use

Load `02_D12_MODEL/D12_granular_masco_classifier.joblib` with joblib. The
artifact is a dictionary containing:

- `pipeline`
- `fallback_vectorizer`
- `fallback_catalog_matrix`
- `catalog`
- `classes`
- `low_confidence_threshold`
- `embedding_class_centroids`
- `selected_research_model`

Do not present it as a raw-resume model. Its input contract is structured prior
occupation history, skill groups, duration, and education. Require user
confirmation for every suggestion.

