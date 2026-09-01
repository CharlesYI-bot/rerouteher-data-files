# Coolify appends the uploaded archive path as $1. Staging only: no SQL runs.
set -eu
umask 077
d13_dir=/var/lib/postgresql/masco2020_migration_20260830.MLQhVm
test -s "$d13_dir/before.dump"
test "$(sha256sum "$d13_dir/before.dump" | cut -d' ' -f1)" = dc6c47767eb7bb533d20e30ffcdc34f71114dc23f1becd5da31cfa3d1ca6e3d7
test "$(sha256sum "$1" | cut -d' ' -f1)" = f71f9e9d7ad0fd02048428067425057b5fb2bf7a276f1ea56a72cd2be15920dd
test ! -e "$d13_dir/migration.sql"
gzip -t "$1"
gzip -dc "$1" > "$d13_dir/migration.sql"
test "$(sha256sum "$d13_dir/migration.sql" | cut -d' ' -f1)" = 9ac887a7301a7a99bf777837daf8389d296b30bb4ba4e891ebff6b0ff2aba7be
printf 'MIGRATION_STAGED_NO_SQL_EXECUTED\n'
sha256sum "$d13_dir/migration.sql"
