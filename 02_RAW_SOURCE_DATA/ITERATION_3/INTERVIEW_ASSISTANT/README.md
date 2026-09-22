# Interview Assistant Raw Sources — Iteration 3

This package contains the source snapshots used to build the ReRouteHer Interview Assistant dataset. The role universe is fixed at 657 MASCO 2020 roles. ESCO, O*NET, NOC and OSCA are used only to enrich those roles with global tasks and skills; they do not add roles.

## Contents

- `MASCO` contains the 657-role project crosswalk derived from MASCO 2020.
- `ESCO` contains ESCO 1.2.1 occupation and occupation-skill relation tables.
- `ONET` contains the O*NET 31.0 occupation, task and skill tables used by the build.
- `NOC` contains the official NOC 2021 Version 1.0 elements extract.
- `OSCA` contains the official OSCA 2024 Version 1.0 workbooks used to normalize Australian role descriptions and tasks.
- `OPEN_QA` contains the pinned open interview-question snapshots, their licence notices, and a cached VA methodology page.
- `source_manifest.csv` records the source, version, licence reference, local file, byte size and SHA-256 digest for every file.

## Licence and release controls

O*NET is distributed under CC BY 4.0. The included 30 Seconds of Interviews snapshot is MIT-licensed. The Continuum interview-question snapshot is CC BY-SA 4.0. Statistics Canada and the Australian Bureau of Statistics publish their data under the licence terms linked in `source_manifest.csv`. ESCO reuse is subject to the European Commission reuse policy.

The MASCO-derived crosswalk is retained for project reproducibility, but the supplied materials do not establish an explicit open-data licence for external bulk redistribution. Confirm DOSM/MOHR permission before mirroring this file beyond the project repository. The VA page is retained only as a methodology snapshot; the processed question bank does not redistribute VA example answers verbatim.
