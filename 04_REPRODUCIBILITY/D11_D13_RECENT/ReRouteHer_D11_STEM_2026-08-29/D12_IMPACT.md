# D12 impact of the corrected D11 scope

The current MASCO classifier must be treated as superseded for the STEM-role requirement. Its local metrics report 19 trained six-digit classes, while the corrected D11 target catalog contains 657 official six-digit eMASCO STEM roles.

## Required D12 target contract

- Prediction key: exact six-digit `masco_code`
- Display field: `masco_code_printed`, such as `2512-01`
- Allowed role catalog: the 657 D11 STEM roles
- Resume source: only the confirmed JobHop v2 2019+ dataset
- ESCO: retained as comparison and auxiliary metadata, not substituted for the MASCO prediction
- Four-digit MASCO unit groups: hierarchy and fallback features only, never the prediction label

## Recommended retraining design

1. Re-label JobHop v2 2019+ against the 657-role D11 catalog using titles, descriptions, and official task text.
2. Require provenance and confidence for every training label; do not fabricate examples for roles with no defensible resume evidence.
3. Train supervised classes only where validated sample support is adequate.
4. Keep all 657 roles available through a catalog/retrieval fallback so sparse roles remain matchable without collapsing the output to a four-digit group.
5. Evaluate exact six-digit accuracy and top-k recall using a role-stratified holdout, plus explicit coverage metrics for supervised and fallback predictions.
6. Preserve ESCO codes/titles in evaluation output for comparison, while scoring MASCO as the authoritative target.
7. Do not replace the production endpoint until the new 657-role target contract, coverage, and validation results are reviewed.

The D11 release does not retrain or deploy D12. It supplies the corrected authoritative target catalog and task text needed for that work.
