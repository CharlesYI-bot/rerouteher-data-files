# ReRouteHer data files

This public repository stores the ReRouteHer Iteration 1 data files from D1-D13. The Data Management Plan is kept separately in the Team Drive.

## Folder structure

- `02_RAW_SOURCE_DATA` contains approved source snapshots and licence records.
- `03_PROCESSED_DATA` contains cleaned tables, mappings, model outputs and review files.
- `04_REPRODUCIBILITY` contains scripts, checks, reports and release records.
- `05_DATABASE_FILES` contains database schemas, migrations, verification SQL and receipts.

Large binary and data files are tracked with Git Large File Storage (Git LFS). Install Git LFS before cloning if the complete files are needed.

## Data handling

Archived resume data and its legacy D9 model artifacts are not included in this repository. JobHop records use pseudonymous identifiers and do not contain email, phone or address fields. Do not commit passwords, API keys, database credentials, private tokens or directly identifying resume text.

## Licence note

JobHop v2 2019+ is recorded as Creative Commons Attribution 4.0 (CC BY 4.0). Other third-party sources keep their original source and licence records in the relevant folders.
