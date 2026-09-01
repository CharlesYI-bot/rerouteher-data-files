# Source policy

## Sole resume/career-history dataset

`jobhop_v2_confirmed_active_2019plus.csv` is the only individual-level
resume/career-history input used by D12. Its SHA-256 is recorded in the source
manifest, dataset profile, metrics, and joblib artifact.

No other resume dataset is read by the D11/D12 build.

## Occupational references (not resume datasets)

- MASCO 2020 official PDF: six-digit occupation codes and titles, parent task
  descriptions, and source-page lineage.
- ESCO official occupation and skill references: standardized titles and skill
  groups used to compose interpretable structured history features.
- Existing D1 role table: unit-group remote/AI pre-ratings and task summaries
  inherited by granular children.

The ESCO-to-MASCO label crosswalk is a transparent project crosswalk, not an
official published crosswalk. It must be reviewed by the domain owner.
