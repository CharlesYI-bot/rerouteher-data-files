# MASCO 657 Global Interview Assistant Dataset — Iteration 3

This release keeps the role universe fixed at the 657 MASCO 2020 roles and enriches those roles with globally sourced interview content. It does not create or import additional roles.

## Release contents

- `ReRouteHer_MASCO657_Global_Interview_Dataset_v3.xlsx` is the review workbook with 12 worksheets.
- `csv` contains one UTF-8 CSV export for every worksheet.
- `normalized` contains the normalized NOC 2021 and OSCA 2024 records used by the build.
- `release_summary.json` records scope and validation counts.

## Coverage

- 657 MASCO roles
- 7,884 generated interview questions
- 1,078 global source matches
- 5,581 role anchors
- 142 open Q&A records
- 320 role-to-open-Q&A links
- ESCO enrichment for 657 roles
- O*NET enrichment for 151 roles
- NOC enrichment for 84 roles
- OSCA enrichment for 186 roles

The workbook separates the generated role question bank from open-source question records. Each generated question includes source lineage, answer guidance, rubric references and review status. Title-similarity matches to O*NET, NOC and OSCA remain candidates for human review.

## Validation

All 11 release checks in `csv/data_quality.csv` passed. The workbook archive integrity check passed, and the CSV export found no spreadsheet formula-error tokens. File digests are recorded in `04_REPRODUCIBILITY/ITERATION_3/INTERVIEW_ASSISTANT/SHA256SUMS.txt`.

## Rights note

Source and licence details are recorded in `csv/sources_and_licences.csv` and the raw source manifest. MASCO redistribution rights require confirmation before an external bulk release. Other source-specific attribution, notice and share-alike obligations remain applicable.
