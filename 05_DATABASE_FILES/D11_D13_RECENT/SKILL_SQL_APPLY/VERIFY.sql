BEGIN READ ONLY;
SET LOCAL search_path=rerouteher,public;
SET LOCAL statement_timeout='60s';
DO $verify$
DECLARE receipt jsonb; x record; h text;
BEGIN
 IF current_database()<>'rerouteher_test' THEN RAISE EXCEPTION 'Wrong database'; END IF;
 SELECT metadata_value INTO STRICT receipt FROM dataset_metadata WHERE metadata_key='skill_bands_fix_20260831.receipt';
 FOR x IN SELECT key AS tbl,value AS expected FROM jsonb_each_text(receipt->'table_hashes') LOOP
  EXECUTE format('SELECT md5(coalesce(string_agg(md5(to_jsonb(t)::text),'''' ORDER BY md5(to_jsonb(t)::text)),'''')) FROM rerouteher.%I t',x.tbl) INTO h;
  IF h<>x.expected THEN RAISE EXCEPTION 'Post-commit fingerprint mismatch: %',x.tbl; END IF;
 END LOOP;
 IF EXISTS(SELECT 1 FROM role_skills r JOIN skill_taxonomy t USING(skill_id) WHERE r.skill_name<>t.canonical_name OR r.skill_type<>t.skill_type) THEN RAISE EXCEPTION 'Master mismatch'; END IF;
 IF EXISTS(SELECT 1 FROM role_skills r FULL JOIN role_skill_lineage l USING(role_id,skill_id) WHERE r.role_id IS NULL OR l.role_id IS NULL OR r.skill_name<>l.skill_name OR r.skill_type<>l.skill_type OR r.importance IS DISTINCT FROM l.importance) THEN RAISE EXCEPTION 'Lineage mismatch'; END IF;
 IF EXISTS(SELECT 1 FROM pg_constraint WHERE connamespace='rerouteher'::regnamespace AND NOT convalidated) THEN RAISE EXCEPTION 'Unvalidated constraint'; END IF;
 IF (SELECT count(*) FROM roles)<>662 OR (SELECT count(*) FROM role_skills)<>23279 THEN RAISE EXCEPTION 'Unexpected counts'; END IF;
 IF EXISTS(SELECT 1 FROM roles r WHERE NOT EXISTS(SELECT 1 FROM role_skills s WHERE s.role_id=r.role_id AND s.skill_type='soft') OR NOT EXISTS(SELECT 1 FROM role_skills s WHERE s.role_id=r.role_id AND s.skill_type='ai_usage')) THEN RAISE EXCEPTION 'Missing band'; END IF;
 RAISE NOTICE 'POST_COMMIT_PASS: four table fingerprints match, canonical classifications and lineage consistent, all constraints validated, all 662 roles have soft and AI usage mappings';
 RAISE NOTICE 'COMMITTED_RECEIPT %',receipt;
 FOR x IN SELECT skill_type,count(*) n FROM role_skills GROUP BY skill_type ORDER BY skill_type LOOP RAISE NOTICE 'BAND %',row_to_json(x); END LOOP;
END $verify$;
ROLLBACK;
