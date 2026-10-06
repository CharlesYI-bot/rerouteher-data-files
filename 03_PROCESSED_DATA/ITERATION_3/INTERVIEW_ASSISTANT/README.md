# MASCO 631 Interview Coach Dataset — Iteration 3

Version 4 is the current release for the interview-practice prototype. It uses the application's 631 canonical roles, keeps the role catalogue fixed, and adds globally grounded question material without importing extra roles.

## Current release

- `v4/ReRouteHer_MASCO631_Interview_Coach_Dataset_v4.xlsx` is the review workbook.
- `v4/csv` contains one UTF-8 CSV export for each worksheet.
- `normalized` contains the normalized NOC 2021 and OSCA 2024 inputs used by the build.
- `release_summary.json` records the v4 scope and validation counts.
- The older MASCO 657 v3 workbook and CSV folder remain as historical output.

## Canonical role boundary

The 657 source-current records map to 655 MASCO 2020 identities. The approved application alias table then consolidates 24 duplicate identities, producing exactly 631 canonical roles. Original identifiers and MASCO codes remain visible through the source and alias columns. The merge map is stored at `02_RAW_SOURCE_DATA/ITERATION_3/INTERVIEW_ASSISTANT/MASCO/canonical_role_merges_20260923.json`.

## Coverage

- 631 canonical roles
- 7,572 role-specific prompts: 12 per role
- 18 reusable general prompts, including conflict and disagreement
- 6 session blueprints for General, Role-specific, and Mixed practice at 5 or 10 questions
- 1,078 global occupation matches and 5,526 role anchors
- 142 licensed open technical questions and 328 reviewed role links
- 10 AI evaluation criteria

The question tables do not contain model answers, answer frameworks, or suggested-answer fields. The product can evaluate each user's transcript against the evidence-focused criteria in `AI Evaluation Rubric`.

The former `employer_question` category is now `questions_for_interviewer`. It asks, “What question would you ask the interviewer if given the opportunity?”, followed by what the user hopes to learn from the answer.

## Validation

All 17 v4 quality checks passed. The workbook formula scan found no spreadsheet error tokens. The CSV schema check confirmed that answer-related fields are absent from General Questions, Role Questions, and Open Questions.

## Rights and review

Source and licence details are in `v4/csv/sources_and_licences.csv`. Open technical questions retain source attribution and currentness-review flags. MASCO redistribution rights still require confirmation before external bulk release. Title-similarity mappings to O*NET, NOC, and OSCA require human review before production use.
