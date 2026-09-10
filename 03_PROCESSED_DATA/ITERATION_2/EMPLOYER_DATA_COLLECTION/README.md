# Employer Data Collection Iteration 2

This directory contains the researched employer dataset for ReRouteHer Iteration 2.

## Dataset

- `ReRouteHer_Iteration2_Employer_Data_70_Qualifying.xlsx`
- `ReRouteHer_Iteration2_Employer_Data_70_Qualifying.csv`
- 70 Bursa-listed companies
- 10 companies in each of seven sector groups
- 24 nonqualifying original candidates retained in the workbook replacement audit
- zero pending company source searches

The primary `Employer Data` table contains one row per company. The dataset owner removed the `collector` field before repository upload. The remaining 23 fields include the company identifiers, source location, family-friendly and flexibility benefits, raw evidence text, and `qa_checked_by` status.

The CSV is a standalone export of the edited `Employer Data` table. It contains one header row and 70 company rows in the same 23-column order.

Raw source documents and the retrieval manifest are stored in `02_RAW_SOURCE_DATA/ITERATION_2/EMPLOYER_DATA_COLLECTION`.

All positive benefit fields remain pending second-person QA. Treat the dataset as researched and source-linked, but not yet QA-approved for production use.
