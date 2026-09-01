-- Read-only verification of the committed data quality update.
\set ON_ERROR_STOP on
BEGIN READ ONLY;
SET LOCAL search_path=rerouteher,public;
SET LOCAL statement_timeout='60s';
DO $verify_receipt$
DECLARE t record; n bigint; fp text; pred text; receipt jsonb; schema_fp text;
BEGIN
 IF current_database()<>'rerouteher_test' THEN RAISE EXCEPTION 'Wrong database'; END IF;
 SELECT metadata_value INTO STRICT receipt FROM dataset_metadata WHERE metadata_key='d13_quality_fix_20260830.receipt';
 FOR t IN SELECT * FROM jsonb_to_recordset(receipt->'expected_table_fingerprints') AS x(table_name text,row_count bigint,row_hash text) LOOP
   pred := CASE WHEN t.table_name='skill_taxonomy' THEN ' WHERE skill_id NOT IN (''ONET_2_A_1_e'',''ONET_2_B_3_e'',''DIGCOMP_3_4'')'
     WHEN t.table_name='dataset_metadata' THEN ' WHERE NOT starts_with(metadata_key,''d13_quality_fix_20260830.'')' ELSE '' END;
   EXECUTE format('SELECT count(*),md5(coalesce(string_agg(md5(to_jsonb(z)::text),'''' ORDER BY md5(to_jsonb(z)::text)),'''')) FROM rerouteher.%I z%s',t.table_name,pred) INTO n,fp;
   IF n<>t.row_count OR fp<>t.row_hash THEN RAISE EXCEPTION 'Post-commit table fingerprint differs: %',t.table_name; END IF;
 END LOOP;
  SELECT md5(jsonb_build_object(
  'columns',(SELECT jsonb_agg(to_jsonb(c) ORDER BY table_name,ordinal_position) FROM information_schema.columns c WHERE table_schema='rerouteher'),
  'constraints',(SELECT jsonb_agg(jsonb_build_array(conrelid::regclass::text,conname,pg_get_constraintdef(oid),convalidated) ORDER BY conrelid::regclass::text,conname) FROM pg_constraint WHERE connamespace='rerouteher'::regnamespace),
  'indexes',(SELECT jsonb_agg(to_jsonb(i) ORDER BY tablename,indexname) FROM pg_indexes i WHERE schemaname='rerouteher'),
  'views',(SELECT jsonb_agg(to_jsonb(v) ORDER BY table_name) FROM information_schema.views v WHERE table_schema='rerouteher'),
  'triggers',(SELECT jsonb_agg(jsonb_build_array(tgrelid::regclass::text,tgname,pg_get_triggerdef(oid),tgenabled) ORDER BY tgrelid::regclass::text,tgname) FROM pg_trigger WHERE tgrelid IN (SELECT oid FROM pg_class WHERE relnamespace='rerouteher'::regnamespace) AND NOT tgisinternal)
 )::text) INTO schema_fp;
 IF schema_fp<>receipt->>'schema_signature' THEN RAISE EXCEPTION 'Schema signature differs'; END IF;
 RAISE NOTICE 'PASS: all 35 table fingerprints and permanent schema match the migration receipt';
END $verify_receipt$;
SELECT 'counts' marker,(SELECT count(*) FROM roles) roles,(SELECT count(*) FROM skill_taxonomy) skills,
 (SELECT count(*) FROM role_skills) role_skills,(SELECT count(*) FROM role_skill_lineage) lineage,
 (SELECT count(*) FROM skill_aliases) aliases;
SELECT 'invalid_duplicate_groups' marker,
 (SELECT count(*) FROM (SELECT lower(regexp_replace(btrim(role_title),'[[:space:]]+',' ','g')) FROM roles GROUP BY 1 HAVING count(*)>1) x) role_titles,
 (SELECT count(*) FROM (SELECT masco_code FROM roles GROUP BY 1 HAVING count(*)>1) x) masco_codes,
 (SELECT count(*) FROM (SELECT lower(regexp_replace(btrim(canonical_name),'[[:space:]]+',' ','g')) FROM skill_taxonomy GROUP BY 1 HAVING count(*)>1) x) skill_names,
 (SELECT count(*) FROM (SELECT role_id,skill_id FROM role_skills GROUP BY 1,2 HAVING count(*)>1) x) role_skill_pairs;
SELECT 'ambiguous_lookup_terms' marker,count(*) FROM (SELECT term FROM (
 SELECT skill_id,lower(btrim(canonical_name)) term FROM skill_taxonomy UNION SELECT skill_id,lower(btrim(alias)) FROM skill_aliases
) x GROUP BY term HAVING count(DISTINCT skill_id)>1) q;
SELECT 'approvals' marker,metadata_value->>'mapping_confidence' confidence,metadata_value->>'use_in_role_skills' approved,count(*)
FROM dataset_metadata WHERE starts_with(metadata_key,'d13_quality_fix_20260830.mapping.') GROUP BY 2,3 ORDER BY 2;
SELECT 'source_core_hash' marker,md5(string_agg(role_id||'|'||skill_id||'|'||skill_name||'|'||skill_type||'|'||importance::integer::text||';','' ORDER BY role_id COLLATE "C",skill_id COLLATE "C"))='5d9fa703798bdf611b436d54e70d8052' matches_csv
FROM role_skills WHERE role_id ~ '^M[0-9]{6}$';
SELECT 'cases' marker,r.role_id,r.role_title,r.esco_code,count(s.skill_id) core_skills FROM roles r LEFT JOIN role_skills s USING(role_id)
WHERE r.role_id IN ('M232102','M151108','M251201','M252403','M254302') GROUP BY r.role_id ORDER BY r.role_id;
SELECT 'valid_shared_esco_groups' marker,count(*) FROM (SELECT esco_code FROM roles GROUP BY esco_code HAVING count(*)>1) q;
COMMIT;
\echo DATA_QUALITY_POSTCHECKS_PASSED
