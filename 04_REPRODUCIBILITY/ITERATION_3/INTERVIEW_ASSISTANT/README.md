# Interview Assistant Reproducibility — Iteration 3

This directory contains the build and export scripts for the current MASCO 631 interview-coach release and the historical MASCO 657 v3 release.

## Scripts

- `extract_global_role_sources.py` normalizes the official NOC and OSCA source files into the processed `normalized` directory.
- `build_masco631_interview_coach_dataset_v4.mjs` rebuilds the 14-sheet v4 workbook using the approved canonical-role alias map. It outputs question-only tables plus an AI evaluation rubric.
- `export_interview_workbook_csv_v4.mjs` exports each v4 workbook sheet as UTF-8 CSV.
- `build_masco657_global_interview_dataset_v3.mjs` rebuilds the 12-sheet workbook from the raw and normalized inputs.
- `export_interview_workbook_csv.mjs` exports each workbook sheet as UTF-8 CSV.

The scripts resolve repository paths relative to this directory. The workbook builder and exporter require the `@oai/artifact-tool` package supplied by the Codex spreadsheet runtime. The normalization script requires Python and `openpyxl`.

## Build order

1. Run `extract_global_role_sources.py`.
2. Run `build_masco631_interview_coach_dataset_v4.mjs`.
3. Run `export_interview_workbook_csv_v4.mjs`, passing the v4 workbook path and `03_PROCESSED_DATA/ITERATION_3/INTERVIEW_ASSISTANT/v4/csv`.
4. Run `generate_release_checksums.mjs`.
5. Review the v4 `data_quality.csv`, the workbook formula scan, source licences, and all human-review flags.

The current build intentionally holds the application role universe at exactly 631 canonical roles. It derives these from 655 MASCO 2020 identities and the approved 24-merge alias table; global standards contribute enrichment records only.
