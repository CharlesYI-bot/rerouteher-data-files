BEGIN READ ONLY;
DO $preserved$
DECLARE t record; predicate text; fp jsonb; actual jsonb := '{}'::jsonb;
        baseline jsonb;
BEGIN
 SELECT metadata_value->'preserved_rows_baseline' INTO STRICT baseline
 FROM rerouteher.dataset_metadata
 WHERE metadata_key='d13_masco2020_migration_20260830.receipt';
 FOR t IN SELECT tablename FROM pg_tables WHERE schemaname='rerouteher' ORDER BY tablename LOOP
   predicate := CASE
     WHEN t.tablename IN ('roles','role_skills','role_skill_lineage') THEN
       'WHERE NOT EXISTS(SELECT 1 FROM rerouteher.dataset_metadata m WHERE m.metadata_key=''d13_masco2020_rebuilt_20260830.mapping.''||z.role_id)'
     WHEN t.tablename IN ('skill_taxonomy','skill_aliases') THEN
       'WHERE NOT EXISTS(SELECT 1 FROM rerouteher.dataset_metadata m WHERE m.metadata_key=''d13_masco2020_rebuilt_20260830.skill_type.''||z.skill_id)'
     WHEN t.tablename='dataset_metadata' THEN
       'WHERE NOT starts_with(metadata_key,''d13_masco2020_rebuilt_20260830.'') AND NOT starts_with(metadata_key,''d13_masco2020_migration_20260830.'')'
     ELSE '' END;
   EXECUTE format('SELECT jsonb_build_object(''rows'',count(*),''md5'',md5(coalesce(string_agg(md5(to_jsonb(z)::text),'''' ORDER BY md5(to_jsonb(z)::text)),''''))) FROM rerouteher.%I z %s',t.tablename,predicate) INTO fp;
   actual := actual || jsonb_build_object(t.tablename,fp);
 END LOOP;
 IF actual IS DISTINCT FROM baseline THEN
   RAISE EXCEPTION 'Post-commit original/unrelated row preservation check failed';
 END IF;
 RAISE NOTICE 'PRESERVED_ROWS_PASS_ALL_35_TABLES';
END $preserved$;
SELECT 'roles' AS item,count(*) FROM rerouteher.roles
UNION ALL SELECT 'skills',count(*) FROM rerouteher.skill_taxonomy
UNION ALL SELECT 'aliases',count(*) FROM rerouteher.skill_aliases
UNION ALL SELECT 'role_skills',count(*) FROM rerouteher.role_skills
UNION ALL SELECT 'role_skill_lineage',count(*) FROM rerouteher.role_skill_lineage
UNION ALL SELECT 'original_roles_R01_R10',count(*) FROM rerouteher.roles WHERE role_id IN ('R01','R02','R03','R04','R05','R06','R07','R08','R09','R10')
UNION ALL SELECT 'MASCO2020_roles',count(*) FROM rerouteher.roles WHERE role_id ~ '^M[0-9]{6}$'
UNION ALL SELECT 'old_role_snapshots',count(*) FROM rerouteher.dataset_metadata WHERE starts_with(metadata_key,'d13_masco2020_migration_20260830.prior_role.')
UNION ALL SELECT 'new_release_metadata',count(*) FROM rerouteher.dataset_metadata WHERE starts_with(metadata_key,'d13_masco2020_rebuilt_20260830.')
UNION ALL SELECT 'ESCO_comparisons',count(*) FROM rerouteher.dataset_metadata WHERE starts_with(metadata_key,'d13_masco2020_rebuilt_20260830.source_esco.');
SELECT metadata_value->>'committed_at' AS committed_at,
       metadata_value->>'schema_signature' AS schema_signature
FROM rerouteher.dataset_metadata
WHERE metadata_key='d13_masco2020_migration_20260830.receipt';
COMMIT;
