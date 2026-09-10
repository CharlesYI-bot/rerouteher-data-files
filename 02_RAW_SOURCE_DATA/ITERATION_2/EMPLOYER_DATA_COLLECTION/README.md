# Employer Data Collection Raw Sources

This directory contains the raw source package for the ReRouteHer Iteration 2 employer dataset.

## Contents

- `PROJECT_REQUIREMENTS` contains the supplied Employer Data Collection Spec and Task List.
- `SOURCE_FILES` contains directly downloadable documents verified as PDFs.
- `employer_source_manifest.csv` lists all 95 cited sources, retrieval outcomes, local filenames, sizes, and SHA-256 checksums.
- `download_summary.json` records package-level counts and the source workbook checksum.

No HTML pages or scraped web content are stored. Sources that are web pages remain URL-only entries in the manifest. Restricted, timed-out, oversized, or otherwise unavailable documents are recorded as download failures instead of being silently omitted.

The archived documents remain the property of their respective publishers. Use the original source URL in the manifest as the authoritative publication location.
