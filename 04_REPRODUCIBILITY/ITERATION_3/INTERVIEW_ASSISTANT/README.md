# Interview Assistant Reproducibility — Iteration 3

This directory contains the build and export scripts for the MASCO 657 global interview dataset.

## Scripts

- `extract_global_role_sources.py` normalizes the official NOC and OSCA source files into the processed `normalized` directory.
- `build_masco657_global_interview_dataset_v3.mjs` rebuilds the 12-sheet workbook from the raw and normalized inputs.
- `export_interview_workbook_csv.mjs` exports each workbook sheet as UTF-8 CSV.

The scripts resolve repository paths relative to this directory. The workbook builder and exporter require the `@oai/artifact-tool` package supplied by the Codex spreadsheet runtime. The normalization script requires Python and `openpyxl`.

## Build order

1. Run `extract_global_role_sources.py`.
2. Run `build_masco657_global_interview_dataset_v3.mjs`.
3. Run `export_interview_workbook_csv.mjs`, passing the workbook path and the processed `csv` directory.
4. Compare outputs against `SHA256SUMS.txt` and review `csv/data_quality.csv`.

The build intentionally holds the role universe at exactly 657 MASCO roles. Global standards contribute enrichment records only.
