# Optional SQL import — separate empty test database only

**Do not run this release as an append to the existing `rerouteher_test`.** Some numeric MASCO IDs are reused for different occupations across versions. In this release, 209 retained IDs have a different normalized title from the same ID in the previous current-portal dataset. Appending by ID would not correctly migrate or trim that database.

The existing live database and its schema have not been touched. No deployment or data replacement is implied by delivery of these files.

`MASCO2020_LOAD_EMPTY_TEST_SCHEMA.sql` is a self-contained, data-only snapshot import. It requires:

1. A **separate database named `rerouteher_masco2020_test`**, already initialized with an empty copy of the existing `rerouteher` schema and its required types/extensions.
2. Empty `roles`, `skill_taxonomy`, `skill_aliases`, `role_skills` and `role_skill_lineage` tables. Other schema tables are untouched.
3. No previous `d13_masco2020_test_20260830.*` metadata.

The SQL refuses the wrong database, nonempty target data tables and duplicate release metadata. It uses one transaction and checks all target counts before commit. It does not contain CREATE, ALTER, DROP, DELETE, TRUNCATE or UPDATE statements, and it does not overwrite records on conflicts. A second execution against an already loaded dataset is deliberately refused, not treated as a migration.

Run the whole file from a client with access to that separately prepared database, for example:

```sh
psql -d rerouteher_masco2020_test -v ON_ERROR_STOP=1 -f MASCO2020_LOAD_EMPTY_TEST_SCHEMA.sql
```

Supply your usual host/user authentication without putting passwords into this file. This example does not create the database or schema. If execution fails, stop and inspect the error; do not bypass the guards to load the current database.

Expected inserted rows:

| Existing table | Rows |
|---|---:|
| roles | 655 |
| skill_taxonomy | 6,051 |
| skill_aliases | 37,521 |
| role_skills | 41,286 |
| role_skill_lineage | 41,286 |
| dataset_metadata — this release prefix only | 8,039 |

The verified live schema restricts skill categories to `technical`, `soft`, or `digital`. The SQL therefore adapts ESCO categories to the same coarse test buckets as the earlier import: 908 digital and 5,143 technical. This is not an official ESCO category crosswalk. Original categories and adapter evidence are retained in `dataset_metadata` under `.skill_type.*`; the CSV source categories are unchanged.

Metadata also preserves all active D13 mappings, all 657 original ESCO comparison records and all 675 remap/exclusion audit rows. No schema columns are added.

The SQL was checked against the supplied schema for column names/required values, guards, transaction structure and expected counts. **It has not been executed against a database.** A future migration of the existing database needs a separate, explicit plan for role references and version collisions; this file intentionally does not attempt that operation.
