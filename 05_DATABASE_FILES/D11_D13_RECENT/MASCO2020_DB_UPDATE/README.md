# MASCO 2020 data-only update for the existing test database

Status: **committed and verified**, 30 August 2026 at 07:25:30 UTC
(15:25:30 Malaysia time). See `live_import_receipt.json` for execution evidence.

The user explicitly approved replacement in Coolify. The full rollback-only
rehearsal passed in 26 seconds and left original counts unchanged. The same
checksum-verified SQL then committed successfully in 23 seconds. All six
independent full-source content comparisons passed. Original/unrelated-row
hashes match across all 35 tables, and normalized before/after schema dumps
are identical. Statistics on the five changed data tables were refreshed.

The obsolete D13 rows have been replaced. The full pre-update backup remains
on persistent storage, and all 657 old D13 role rows are additionally archived
in the existing metadata table. Do not rerun the committed migration.

Target: `rerouteher_test`, schema `rerouteher`, in Coolify resource
`postgresql-database-wxnjpd2ia8avtwbs739mtamk`.

The current database was inspected in Safari on 30 August 2026. It contains
35 original tables, 657 prior D13 roles plus R01–R10, 6,205 skills, 38,285
aliases and 41,118 rows in each role-skill table. No outside table references
to the D13 role/skill identities were found, and no user triggers exist on
the five target data tables. Guards recheck these conditions under locks.

## Backup

A full custom-format `pg_dump` backup was created on persistent storage:

`/var/lib/postgresql/masco2020_migration_20260830.MLQhVm/before.dump`

The backup archive listing was successfully read with `pg_restore -l`.
SHA-256: `dc6c47767eb7bb533d20e30ffcdc34f71114dc23f1becd5da31cfa3d1ca6e3d7`.
This is an archive-integrity check, not a completed restore rehearsal.

The same directory contains `before.schema.sql`,
`before.schema.normalized.sql` and `backup_contents.txt`.
The normalized schema excludes only randomized psql restrict/unrestrict lines.
Schema SHA-256: `07cdc5de3a8721e6557717a407fad933968dffde541a441c993b6eacf1925ff1`.

## Replacement scope

The migration replaces only the old D13 dataset with the verified 655-role
MASCO 2020 release. It retains the original 10 roles, their skills/links,
all unrelated rows and all historical metadata. Old D13 role rows are also
archived in the existing `dataset_metadata` table before code reuse.

382 superseded role IDs and 130 old-only skill IDs are removed from active
tables. 380 new role IDs and 46 new skill IDs are added. Overlapping IDs
are refreshed from the new release. Old D13 links and aliases are replaced
with the new release's exact sets. ESCO Title Case displays, lowercase
matching aliases and all 657 original ESCO comparison records are retained.

Verified totals (including preserved original data):

| Table | Before | After |
|---|---:|---:|
| roles | 667 | 665 |
| skill_taxonomy | 6,205 | 6,121 |
| skill_aliases | 38,285 | 37,730 |
| role_skills | 41,118 | 41,194 |
| role_skill_lineage | 41,118 | 41,194 |

No CREATE, ALTER, DROP or TRUNCATE is used. No foreign-key checks are
disabled. One transaction checks baseline ownership/counts, dependencies,
vectors, link consistency, preserved-row hashes and a schema signature.
Failure rolls back the complete migration. Concurrent writes are blocked
briefly by transaction-scoped locks, with a 15-second lock timeout.

## Execution reference — already completed; do not rerun

Use psql, not pg_restore. The SQL defaults to a full rehearsal with ROLLBACK.

```sh
psql -X -v ON_ERROR_STOP=1 -v d13_dry_run=true -U "$POSTGRES_USER" -d rerouteher_test -f MASCO2020_UPDATE_EXISTING_TEST_DATABASE.sql
```

After successful rehearsal and verification that the database is unchanged:

```sh
psql -X -v ON_ERROR_STOP=1 -v d13_dry_run=false -U "$POSTGRES_USER" -d rerouteher_test -f MASCO2020_UPDATE_EXISTING_TEST_DATABASE.sql
```

Then compare a fresh normalized schema dump against the saved one and verify
the counts and migration receipt. Do not repeat a committed migration; its
guards deliberately refuse a second run. Do not restore the backup over the
live database without separate review and authorization.

The mappings remain project test proxies, not an official MASCO–ESCO
equivalence crosswalk. This update does not retrain or deploy a model.
