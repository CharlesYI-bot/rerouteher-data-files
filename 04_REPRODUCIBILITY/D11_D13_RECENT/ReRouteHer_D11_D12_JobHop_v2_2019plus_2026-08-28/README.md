# ReRouteHer D11–D12 handoff

This package implements the newly supplied D11 and D12 tasks on top of the
2026-08-27 high-standard data release.

The MASCO role-code rule is strict: every D11 role and every D12 target,
prediction, class, and catalogue key is exactly six digits. The printed MASCO
form (for example, `2512-01`) is retained only as a display/source field; the
stored role code is `251201`. Four-digit values are parent-group lineage and are
never used as D11 role labels or D12 predictions.

## Resume-data scope

JobHop v2 confirmed-active 2019+ is the only resume/career-history dataset used.
The approved file contains 47,224 work-experience records for 35,568 resumes.
MASCO and ESCO are used only as occupational reference sources for codes,
titles, tasks, and skill groups; they are not additional resume datasets.

## D11 result

- 258 unique six-digit MASCO occupations across the ten curated parent groups.
- Ten curated roles are updated to exact six-digit anchor occupations.
- The other 248 granular children are added with stable `M<masco_code>` IDs.
- All roles have 384-dimensional `all-MiniLM-L6-v2` embeddings.
- Remote/AI ratings inherit the D1 unit-group pre-rating, as permitted by the
  brief; child-specific two-rater review remains an explicit gate.
- The database migration updates the ten existing roles, inserts the remaining
  children, and fails if any four-digit/non-six-digit MASCO role code remains.

Primary files:

- `01_D11_REFERENCE_TABLES/D11_masco_granular_roles.csv`
- `01_D11_REFERENCE_TABLES/D11_curated_role_anchor_map.csv`
- `01_D11_REFERENCE_TABLES/D11_masco_granular_lineage.csv`
- `03_DATABASE/D11_roles_six_digit_migration.sql`

## D12 result

- 562 transition examples reconstructed directly from JobHop v2 2019+ while
  preserving the established train/validation/test split contract.
- 41 pre-merge granular labels; thin labels with fewer than five training
  examples are transparently merged to a six-digit curated anchor in the same
  MASCO parent group, leaving 19 trainable classes.
- Required classifier: word + character `char_wb` TF-IDF with balanced logistic
  regression.
- Required second tier: character-TFIDF retrieval over all 258 D11 roles.
- Benchmark: MiniLM class-centroid retrieval on the identical JobHop split.
- The joblib artifact contains the classifier pipeline, fallback vectorizer and
  matrix, full six-digit catalogue, confidence threshold, MiniLM centroids, and
  label metadata.

Held-out research results:

| Model | Validation accuracy | Validation macro-F1 | Test accuracy | Test macro-F1 |
|---|---:|---:|---:|---:|
| Word + char TF-IDF logistic regression | 19.35% | 15.25% | 20.00% | 11.88% |
| MiniLM centroid benchmark | 27.42% | 17.88% | 24.44% | 14.45% |

The MiniLM benchmark wins on validation macro-F1, but neither model is approved
for automatic production use. The confidence/fallback path is retained in the
artifact; validation calibration selected a low threshold because the full
catalogue fallback otherwise reduced held-out accuracy. Predictions must be
shown as suggestions and confirmed by the user.

Primary files:

- `02_D12_MODEL/D12_granular_masco_classifier.joblib`
- `02_D12_MODEL/D12_training_examples_jobhop_v2_2019plus.csv`
- `02_D12_MODEL/D12_esco_to_masco_label_crosswalk.csv`
- `02_D12_MODEL/D12_metrics.json`
- `02_D12_MODEL/D12_inference_policy.json`

## Quality status

The validation suite contains 31 passing checks and no failures. It verifies
six-digit code formatting, 258 unique D11 codes, embedding dimensions, JobHop
source hashes and split counts, crosswalk integrity, artifact reproducibility,
full-catalogue fallback structure, prediction validity, and the SQL migration
guard.

This is a research/prototype handoff. Production blockers are recorded in
`D12_metrics.json`: geographic transfer, absence of raw CV text, a project-level
ESCO-to-MASCO crosswalk requiring domain review, sparse-label merges, and
inherited child ratings.

