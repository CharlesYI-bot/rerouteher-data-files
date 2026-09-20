# Employer Data Collection Raw Sources — Iteration 3

This directory contains the raw source package for the ReRouteHer Iteration 3 Bursa Malaysia employer dataset.

## Contents

- `SOURCE_FILES` contains 245 downloaded documents validated as PDFs.
- `employer_source_manifest.csv` lists all 245 unique cited report URLs, retrieval outcomes, local filenames, sizes, page counts, and SHA-256 checksums.
- `download_summary.json` records package-level counts and input/output checksums.

The 260 employer rows share some report URLs, so each unique report is archived once and linked through `source_id`. All 245 unique source entries have a validated local PDF, and no HTML pages or scraped web content are stored.

The manifest preserves the original citation as `source_url` and records the exact retrieved endpoint as `final_url`. Most alternate endpoints are exact report mirrors or report parts. Three unavailable citations use a newer same-company substitute and are explicitly labelled in `retrieval_note`: `SRC-123` (Kretam 2025 for the inaccessible 2024 attachment), `SRC-204` (Maxis 2023 for the non-resolving 2022 host), and `SRC-233` (MTT Shipping Sustainability Statement 2025 for the withdrawn prospectus endpoint). These three rows require citation-level QA before production use.

The archived documents remain the property of their respective publishers.
