# D13 rebuilt import — empty test schema only

`MASCO2020_LOAD_EMPTY_TEST_SCHEMA.sql` embeds all data for the rebuilt D13 release. It does not change the schema and has **not been executed**.

It requires a separate database called `rerouteher_masco2020_test`, already initialized with an empty copy of the existing `rerouteher` schema, including the existing `vector(384)` types/extensions. The five target data tables must be empty:

| Table | Inserted rows |
|---|---:|
| roles | 655 |
| skill_taxonomy | 6,080 |
| skill_aliases | 37,654 |
| role_skills | 41,024 |
| role_skill_lineage | 41,024 |
| dataset_metadata — rebuilt release prefix | 8,068 |

The release prefix is `d13_masco2020_rebuilt_20260830`. Metadata retains mappings, raw skill types, all 657 original ESCO comparison records and the original 675-row MASCO version crosswalk. ESCO display titles and canonical/link skill names use the same corrected Title Case as the CSVs. Matching aliases remain lowercase.

The import refuses the wrong database, nonempty target tables and existing rebuilt-release metadata. There are no CREATE, ALTER, DROP, DELETE, TRUNCATE or UPDATE statements. It neither overwrites nor silently skips conflicts. One transaction checks row counts before commit. Re-running against an already loaded database is deliberately refused.

After separately preparing that empty database/schema, run the entire file, for example:

```sh
psql -d rerouteher_masco2020_test -v ON_ERROR_STOP=1 -f MASCO2020_LOAD_EMPTY_TEST_SCHEMA.sql
```

Use your normal host/user authentication; do not put passwords in the file. This command does not create the database or schema. The SQL file is plain text, not a pg_restore archive.

**Do not bypass the guards to append to `rerouteher_test`, or to a populated earlier MASCO 2020 test database.** Numeric MASCO IDs can collide across versions, and this rebuild also changes 16 ESCO assignments and display names. A safe replacement/migration of existing rows and references is a separate task. SQL checks in this package are structural/source checks, not a completed database execution test.
