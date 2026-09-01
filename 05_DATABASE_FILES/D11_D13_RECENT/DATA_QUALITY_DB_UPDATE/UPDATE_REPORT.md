# Database update completed — 30 August 2026

Updated `rerouteher_test` on `postgresql-database-wxnjpd2ia8avtwbs739mtamk` at **17:00:51 Malaysia time**. The permanent 35-table database structure is unchanged. No backend, model or other database was modified.

## Verified result

| Check | Live result |
|---|---:|
| Duplicate normalized role-title groups | 0 |
| Duplicate MASCO-code groups | 0 |
| Duplicate normalized canonical skill-name groups | 0 |
| Duplicate role–skill pairs | 0 |
| Ambiguous exact lookup terms across skill IDs | 0 |
| Role–skill labels/types inconsistent with taxonomy | 0 |
| Unvalidated foreign-key constraints | 0 |

The 655 six-digit MASCO 2020 STEM roles remain intact. Their ESCO comparisons were preserved, including **143 legitimately shared ESCO-code groups**. Sharing an ESCO comparison code does not make distinct MASCO occupations duplicates.

The database now holds 662 roles: the 655 STEM roles plus seven retained historical D1 roles. The latter remain group-level identities awaiting a separate six-digit review; no replacement codes were invented.

## Data applied

- **442 mappings approved** under the user's rule: 117 High and 325 Medium. Their relationship labels were not converted to “exact.”
- **213 Low-confidence mappings remain pending**, with comparison codes retained and their required-skill links held out.
- **13,147 approved D13 core candidate links**, plus 119 retained legacy links: **13,266 active role–skill links** in total.
- 6,121 canonical skill concepts and 37,284 active aliases. Shared concepts consistently retain their IDs.
- Teacher, Vocational has 11 core candidates rather than its prior 115-item essential-plus-optional inventory. Village Community Center Manager remains in the catalog with its ESCO comparison, but has no active core links because its mapping is Low confidence.

## Cleanup and recovery

Retired `R01`, `R02`, and `R06` into `M251201`, `M252403`, and `M254302`, respectively. All **109 linked training examples** and other historical references were preserved and reassigned. The three retired role IDs no longer appear in the role catalog.

Archived and removed 27,911 superseded role–skill rows, 27,928 affected lineage rows, and 446 ambiguous alias rows from active tables. Original values—including rows whose labels or review status changed—remain in the existing `dataset_metadata` table under `d13_quality_fix_20260830.archive.*`. No permanent archive tables or columns were added.

A fresh approximately 39 MB full backup is retained on the PostgreSQL persistent volume:

`/var/lib/postgresql/d13_quality_apply_20260830.pxD2jB/before.dump`

SHA-256: `47d7f2d2ee9cf5c1877962a4b8af213aa24af985f785fae1a69b0a27b9c06f50`

The archive listing was checked. A full restore was not executed or tested. Recovery should be scoped and reviewed; restoring this full backup indiscriminately would also revert unrelated later database changes.

## Verification performed

The source dataset passed 12 local regression tests. A full PostgreSQL migration rehearsal passed and rolled back in **13 seconds**. The same checksum-verified SQL then committed in **14 seconds**.

Independent, read-only post-commit checks verified all 35 expected table fingerprints, the unchanged schema signature, exact agreement between the approved core CSV and live rows, duplicate counts, mapping approvals and representative roles. The recorded schema signature before and after is `a4badd11ae51e535e54d9425dbf656a2`.

Coolify's general restore control was not used: the safety check blocked that route. The file was staged without SQL execution, then the explicitly approved bounded migration was run through `psql` in the database terminal. Server-side `rehearsal.log`, `commit.log`, `postchecks.log` and `schema_before.sql` are retained alongside the backup.

## Still outside this update

The backend was neither edited nor restarted. Its in-memory skill-alias lookup needs a reload/restart to pick up the alias cleanup. Its existing shared-ESCO role-selection, low-confidence recommendation and readiness-scoring issues remain. This update fixes the database contents; it does not claim to resolve those application behaviours or calibrate the test mappings for production.

The machine-readable result is in `live_update_receipt.json`. `preparation.json` records the earlier pre-execution state; the live receipt is the authoritative completion record.
