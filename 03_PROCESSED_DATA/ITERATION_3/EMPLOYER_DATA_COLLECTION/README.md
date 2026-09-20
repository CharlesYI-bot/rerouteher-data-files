# Employer Data Collection — Iteration 3

This directory contains the processed ReRouteHer Iteration 3 Bursa Malaysia employer dataset.

## Dataset

- `ReRouteHer_Iteration3_Employer_Data_260_Qualifying.xlsx` — formatted research tracker workbook.
- `ReRouteHer_Iteration3_Employer_Data_260_Qualifying.csv` — flat 260-row export enriched with raw-source archive fields.
- `ReRouteHer_Iteration3_Employer_Data_260_Qualifying.json` — structured export with research metadata and enriched rows.
- `ReRouteHer_Iteration3_Sector_Summary.csv` — sector-level company, pillar, and downloaded-report counts.
- 260 Bursa-listed company rows across 13 sectors, with 20 rows per sector.
- 245 unique source records and 245 validated local PDFs; duplicates are linked through `source_id`.

The processed CSV and JSON add `source_id`, `local_report_file`, `source_download_status`, `source_sha256`, and `source_pdf_pages` so each row can be traced to the raw archive. Raw source documents and the retrieval manifest are stored in `02_RAW_SOURCE_DATA/ITERATION_3/EMPLOYER_DATA_COLLECTION`.

Pillar flags and cited passages are research results, not second-person QA approval. Consult `qa_checked_by` before treating a row as production-validated. The raw manifest also labels three newer same-company substitute documents that need citation-level QA.
