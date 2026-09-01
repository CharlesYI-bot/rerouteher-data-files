-- DATA ONLY. Existing permanent schema/constraints/indexes are not changed.
-- Target: rerouteher_test / postgresql-database-wxnjpd2ia8avtwbs739mtamk.
-- Requires fresh backup and action-time deletion approval before execution.
-- HOLD LIVE COMMIT: core-only data exposes the deployed empty-band scoring bug.
-- Also requires tested backend compatibility: -v backend_compatibility_confirmed=true
-- Default: transaction rehearsal with ROLLBACK. Commit: -v fix_commit=true
-- Supply -v backup_path=/validated/path/before.dump -v backup_sha256=...
\set ON_ERROR_STOP on
\if :{?fix_commit}
\else
\set fix_commit false
\endif
\if :{?backend_compatibility_confirmed}
\else
\set backend_compatibility_confirmed false
\endif
\if :fix_commit
\if :backend_compatibility_confirmed
\else
\echo STOP: fix and test role resolution, skill IDs, and empty-band scoring before activating this data
\quit 3
\endif
\endif
\if :{?backup_path}
\else
\echo STOP: backup_path is required
\quit 3
\endif
\if :{?backup_sha256}
\else
\echo STOP: backup_sha256 is required
\quit 3
\endif
BEGIN;
SET LOCAL lock_timeout='15s';
SET LOCAL statement_timeout='5min';
SET LOCAL application_name='rerouteher_data_quality_fix_20260830';
SET LOCAL search_path=rerouteher,public;
SELECT set_config('quality_fix.backup_path', :'backup_path', true),
       set_config('quality_fix.backup_sha256', :'backup_sha256', true);

-- Temporary work tables disappear at transaction end; original 35-table schema stays intact.
CREATE TEMP TABLE fix_role_map(old_id text PRIMARY KEY, new_id text UNIQUE) ON COMMIT DROP;
INSERT INTO fix_role_map VALUES ('R01','M251201'),('R02','M252403'),('R06','M254302');
CREATE TEMP TABLE fix_skill_patch(skill_id text PRIMARY KEY, old_name text, old_definition text,
 canonical_name text, skill_type text, embedding_text text) ON COMMIT DROP;
INSERT INTO fix_skill_patch VALUES
@@SKILL_PATCHES@@;
CREATE TEMP TABLE fix_alias_remove(skill_id text, alias text, reason text, PRIMARY KEY(skill_id,alias)) ON COMMIT DROP;
CREATE TEMP TABLE fix_expected(table_name text PRIMARY KEY, row_count bigint, row_hash text) ON COMMIT DROP;
CREATE TEMP TABLE fix_mapping(role_id text PRIMARY KEY, esco_code text, mapping_relation text,
 mapping_confidence text, approved boolean, review_status text) ON COMMIT DROP;
INSERT INTO fix_mapping VALUES
@@MAPPING_APPROVALS@@;

DO $guard$
DECLARE t record; n bigint; fp text;
BEGIN
 IF current_database()<>'rerouteher_test' THEN RAISE EXCEPTION 'Wrong database'; END IF;
 IF current_setting('quality_fix.backup_sha256') !~ '^[a-f0-9]{64}$'
    OR current_setting('quality_fix.backup_path') NOT LIKE '/var/lib/postgresql/%/before.dump'
 THEN RAISE EXCEPTION 'A verified persistent backup is required'; END IF;
 IF NOT pg_try_advisory_xact_lock(hashtext('d13_quality_fix_20260830')) THEN RAISE EXCEPTION 'Another quality migration is running'; END IF;
 FOR t IN SELECT tablename FROM pg_tables WHERE schemaname='rerouteher' ORDER BY tablename LOOP
   EXECUTE format('LOCK TABLE rerouteher.%I IN SHARE ROW EXCLUSIVE MODE', t.tablename);
 END LOOP;
 IF (SELECT count(*) FROM pg_tables WHERE schemaname='rerouteher')<>35
 OR (SELECT count(*) FROM roles)<>665 OR (SELECT count(*) FROM skill_taxonomy)<>6121
 OR (SELECT count(*) FROM role_skills)<>41177 OR (SELECT count(*) FROM role_skill_lineage)<>41194
 OR (SELECT count(*) FROM skill_aliases)<>37730 THEN RAISE EXCEPTION 'Live baseline changed; inspect, do not overwrite'; END IF;
 IF EXISTS(SELECT 1 FROM dataset_metadata WHERE starts_with(metadata_key,'d13_quality_fix_20260830.'))
 THEN RAISE EXCEPTION 'Already applied or prefix in use'; END IF;
 IF NOT EXISTS(SELECT 1 FROM roles WHERE role_id='R01' AND role_title='duplicate' AND masco_code='0' AND esco_code='0')
 OR NOT EXISTS(SELECT 1 FROM roles WHERE role_id='R02' AND role_title='Data Analyst' AND masco_code='2524')
 OR NOT EXISTS(SELECT 1 FROM roles WHERE role_id='R06' AND role_title='Graphic Designer' AND masco_code='2543')
 THEN RAISE EXCEPTION 'Legacy role identity changed'; END IF;
 IF (SELECT count(*) FROM roles WHERE (role_id,role_title,masco_code) IN
   (('M251201','Software Developer','251201'),('M252403','Data Analyst','252403'),('M254302','Graphic Designer','254302')))<>3
 THEN RAISE EXCEPTION 'Canonical MASCO targets do not match reviewed map'; END IF;
 IF (SELECT count(*) FROM fix_mapping WHERE approved)<>442
 OR EXISTS(SELECT 1 FROM fix_mapping m LEFT JOIN roles r USING(role_id) WHERE r.role_id IS NULL OR r.esco_code<>m.esco_code)
 OR EXISTS(SELECT 1 FROM fix_mapping WHERE approved IS DISTINCT FROM (mapping_confidence IN ('medium','high')))
 THEN RAISE EXCEPTION 'Mapping approval rule or live ESCO comparison changed'; END IF;
 IF (SELECT count(*) FROM role_skills WHERE role_id IN ('R01','R02','R06'))<>34
 OR (SELECT count(*) FROM role_skill_lineage WHERE role_id IN ('R01','R02','R06'))<>51
 THEN RAISE EXCEPTION 'Legacy requirement baseline changed'; END IF;
 SELECT md5(string_agg(role_id||'|'||skill_id||'|'||importance::integer::text||';','' ORDER BY role_id COLLATE "C",skill_id COLLATE "C"))
 INTO fp FROM role_skills WHERE role_id ~ '^M[0-9]{6}$';
 IF fp<>'@@PAIR_HASH@@' THEN RAISE EXCEPTION 'D13 requirement pairs differ from reviewed source'; END IF;
 IF EXISTS(SELECT 1 FROM fix_skill_patch p LEFT JOIN skill_taxonomy s USING(skill_id)
  WHERE s.skill_id IS NULL OR s.canonical_name<>p.old_name OR s.definition<>p.old_definition
  OR s.embedding_model<>'sentence-transformers/all-MiniLM-L6-v2')
 THEN RAISE EXCEPTION 'Framework concept definitions changed'; END IF;
 -- Do not silently merge colliding historical records. All target child sets were audited empty.
 FOR t IN SELECT table_name FROM information_schema.columns WHERE table_schema='rerouteher'
   AND column_name='role_id' AND table_name NOT IN ('roles','role_skills','role_skill_lineage') LOOP
   EXECUTE format('SELECT count(*) FROM rerouteher.%I WHERE role_id IN (SELECT new_id FROM fix_role_map)',t.table_name) INTO n;
   IF n<>0 THEN RAISE EXCEPTION 'Historical target collision in %; review manually',t.table_name; END IF;
 END LOOP;
 -- Foreign keys in unexpected schemas would need a separately reviewed migration.
 IF EXISTS(SELECT 1 FROM pg_constraint c JOIN pg_class child ON child.oid=c.conrelid
  WHERE c.contype='f' AND c.confrelid IN ('rerouteher.roles'::regclass,'rerouteher.skill_taxonomy'::regclass)
  AND child.relnamespace<>'rerouteher'::regnamespace) THEN RAISE EXCEPTION 'External schema dependencies found'; END IF;
 SELECT md5(jsonb_build_object(
  'columns',(SELECT jsonb_agg(to_jsonb(c) ORDER BY table_name,ordinal_position) FROM information_schema.columns c WHERE table_schema='rerouteher'),
  'constraints',(SELECT jsonb_agg(jsonb_build_array(conrelid::regclass::text,conname,pg_get_constraintdef(oid),convalidated) ORDER BY conrelid::regclass::text,conname) FROM pg_constraint WHERE connamespace='rerouteher'::regnamespace),
  'indexes',(SELECT jsonb_agg(to_jsonb(i) ORDER BY tablename,indexname) FROM pg_indexes i WHERE schemaname='rerouteher'),
  'views',(SELECT jsonb_agg(to_jsonb(v) ORDER BY table_name) FROM information_schema.views v WHERE table_schema='rerouteher'),
  'triggers',(SELECT jsonb_agg(jsonb_build_array(tgrelid::regclass::text,tgname,pg_get_triggerdef(oid),tgenabled) ORDER BY tgrelid::regclass::text,tgname) FROM pg_trigger WHERE tgrelid IN (SELECT oid FROM pg_class WHERE relnamespace='rerouteher'::regnamespace) AND NOT tgisinternal)
 )::text) INTO fp;
 PERFORM set_config('quality_fix.schema_before',fp,true);
END $guard$;

-- Unique canonical labels outrank aliases. Other ambiguous labels are held for review,
-- not resolved to an arbitrary concept. Compute against the POST-PATCH canonical labels.
INSERT INTO fix_alias_remove
WITH canonical AS (
 SELECT s.skill_id,lower(btrim(coalesce(p.canonical_name,s.canonical_name))) term
 FROM skill_taxonomy s LEFT JOIN fix_skill_patch p USING(skill_id)
), terms AS (
 SELECT * FROM canonical UNION SELECT skill_id,lower(btrim(alias)) FROM skill_aliases
), ambiguous AS (
 SELECT term FROM terms GROUP BY term HAVING count(DISTINCT skill_id)>1
)
SELECT a.skill_id,a.alias,
 CASE WHEN EXISTS(SELECT 1 FROM canonical c WHERE c.term=lower(btrim(a.alias)))
 THEN 'Canonical Label Takes Priority' ELSE 'Ambiguous Alias Requires Contextual Review' END
FROM skill_aliases a JOIN ambiguous x ON x.term=lower(btrim(a.alias))
WHERE NOT EXISTS(SELECT 1 FROM canonical c WHERE c.term=x.term AND c.skill_id=a.skill_id);
DO $alias_guard$ BEGIN
 IF (SELECT count(*) FROM fix_alias_remove)<>@@ALIAS_REMOVALS@@
 THEN RAISE EXCEPTION 'Alias review set changed'; END IF;
END $alias_guard$;

-- Archive exact original affected rows and compute expected full-table fingerprints.
-- Historical resume contents stay inside the same database; no content is printed.
DO $archive$
DECLARE t record; pred text; expected_query text; payload jsonb; n bigint; fp text;
BEGIN
 FOR t IN SELECT tablename FROM pg_tables WHERE schemaname='rerouteher' ORDER BY tablename LOOP
   pred := 'FALSE';
   expected_query := format('SELECT to_jsonb(z) j FROM rerouteher.%I z',t.tablename);
   IF t.tablename='roles' THEN
     pred := 'z.role_id IN (SELECT old_id FROM fix_role_map)';
     expected_query := expected_query || ' WHERE NOT ('||pred||')';
   ELSIF t.tablename='skill_taxonomy' THEN
     pred := 'z.skill_id IN (SELECT skill_id FROM fix_skill_patch)';
     -- The three replacement vectors/names are checked separately after mutation.
     expected_query := expected_query || ' WHERE NOT ('||pred||')';
   ELSIF t.tablename='skill_aliases' THEN
     pred := 'EXISTS(SELECT 1 FROM fix_alias_remove a WHERE a.skill_id=z.skill_id AND a.alias=z.alias)';
     expected_query := expected_query || ' WHERE NOT ('||pred||')';
   ELSIF t.tablename IN ('role_skills','role_skill_lineage') THEN
     pred := 'z.role_id IN (SELECT old_id FROM fix_role_map) OR z.role_id IN (SELECT role_id FROM fix_mapping WHERE NOT approved) OR (z.role_id ~ ''^M[0-9]{6}$'' AND z.importance=50) OR z.skill_id IN (SELECT skill_id FROM fix_skill_patch)';
     expected_query := format('SELECT to_jsonb(z) || CASE WHEN p.skill_id IS NOT NULL THEN jsonb_build_object(''skill_name'',p.canonical_name,''skill_type'',p.skill_type) ELSE ''{}''::jsonb END j FROM rerouteher.%I z LEFT JOIN fix_skill_patch p USING(skill_id) WHERE z.role_id NOT IN (SELECT old_id FROM fix_role_map) AND z.role_id NOT IN (SELECT role_id FROM fix_mapping WHERE NOT approved) AND NOT (z.role_id ~ ''^M[0-9]{6}$'' AND z.importance=50)',t.tablename);
   ELSIF t.tablename='dataset_metadata' THEN
     expected_query := expected_query || ' WHERE NOT starts_with(metadata_key,''d13_quality_fix_20260830.'')';
   ELSIF EXISTS(SELECT 1 FROM information_schema.columns WHERE table_schema='rerouteher' AND table_name=t.tablename AND column_name='role_id') THEN
     pred := 'z.role_id IN (SELECT old_id FROM fix_role_map)';
     expected_query := format('SELECT to_jsonb(z) || CASE WHEN m.old_id IS NOT NULL THEN jsonb_build_object(''role_id'',m.new_id) ELSE ''{}''::jsonb END j FROM rerouteher.%I z LEFT JOIN fix_role_map m ON z.role_id=m.old_id',t.tablename);
   END IF;
   EXECUTE format('SELECT coalesce(jsonb_agg(to_jsonb(z)),''[]''::jsonb) FROM rerouteher.%I z WHERE %s',t.tablename,pred) INTO payload;
   IF jsonb_array_length(payload)>0 THEN
     INSERT INTO dataset_metadata VALUES ('d13_quality_fix_20260830.archive.'||t.tablename,payload);
   END IF;
   EXECUTE 'SELECT count(*),md5(coalesce(string_agg(md5(j::text),'''' ORDER BY md5(j::text)),'''')) FROM ('||expected_query||') q' INTO n,fp;
   INSERT INTO fix_expected VALUES(t.tablename,n,fp);
 END LOOP;
END $archive$;

-- Optional skills are retained as conditional data in the archive and versioned CSV.
-- Essential links are only test core CANDIDATES, not validated MASCO equivalences.
DELETE FROM role_skills WHERE role_id IN (SELECT old_id FROM fix_role_map)
 OR role_id IN (SELECT role_id FROM fix_mapping WHERE NOT approved)
 OR (role_id ~ '^M[0-9]{6}$' AND importance=50);
DELETE FROM role_skill_lineage WHERE role_id IN (SELECT old_id FROM fix_role_map)
 OR role_id IN (SELECT role_id FROM fix_mapping WHERE NOT approved)
 OR (role_id ~ '^M[0-9]{6}$' AND importance=50);
DELETE FROM skill_aliases a USING fix_alias_remove x WHERE a.skill_id=x.skill_id AND a.alias=x.alias;
UPDATE skill_taxonomy s SET canonical_name=p.canonical_name,skill_type=p.skill_type,embedding=p.embedding_text::vector
 FROM fix_skill_patch p WHERE s.skill_id=p.skill_id;
UPDATE role_skills r SET skill_name=p.canonical_name,skill_type=p.skill_type FROM fix_skill_patch p WHERE r.skill_id=p.skill_id;
UPDATE role_skill_lineage r SET skill_name=p.canonical_name,skill_type=p.skill_type FROM fix_skill_patch p WHERE r.skill_id=p.skill_id;
DO $reparent$
DECLARE t record;
BEGIN
 FOR t IN SELECT table_name FROM information_schema.columns WHERE table_schema='rerouteher' AND column_name='role_id'
 AND table_name NOT IN ('roles','role_skills','role_skill_lineage') ORDER BY table_name LOOP
   EXECUTE format('UPDATE rerouteher.%I z SET role_id=m.new_id FROM fix_role_map m WHERE z.role_id=m.old_id',t.table_name);
 END LOOP;
END $reparent$;
DELETE FROM roles WHERE role_id IN (SELECT old_id FROM fix_role_map);

DO $verify$
DECLARE t record; pred text; n bigint; fp text; schema_fp text;
BEGIN
 FOR t IN SELECT * FROM fix_expected LOOP
   pred := CASE WHEN t.table_name='skill_taxonomy' THEN ' WHERE skill_id NOT IN (SELECT skill_id FROM fix_skill_patch)'
     WHEN t.table_name='dataset_metadata' THEN ' WHERE NOT starts_with(metadata_key,''d13_quality_fix_20260830.'')' ELSE '' END;
   EXECUTE format('SELECT count(*),md5(coalesce(string_agg(md5(to_jsonb(z)::text),'''' ORDER BY md5(to_jsonb(z)::text)),'''')) FROM rerouteher.%I z%s',t.table_name,pred) INTO n,fp;
   IF n<>t.row_count OR fp<>t.row_hash THEN RAISE EXCEPTION 'Unexpected data change in %; rolling back',t.table_name; END IF;
 END LOOP;
 IF EXISTS(SELECT 1 FROM fix_skill_patch p JOIN skill_taxonomy s USING(skill_id)
  WHERE s.canonical_name<>p.canonical_name OR s.skill_type<>p.skill_type OR s.definition<>p.old_definition
    OR s.embedding::text<>(p.embedding_text::vector)::text) THEN RAISE EXCEPTION 'Skill patch mismatch'; END IF;
 IF (SELECT count(*) FROM roles)<>662 OR (SELECT count(*) FROM role_skills)<>13266
 OR (SELECT count(*) FROM role_skill_lineage)<>13266 THEN RAISE EXCEPTION 'Incorrect final totals'; END IF;
 IF (SELECT count(*) FROM roles WHERE role_id ~ '^M[0-9]{6}$' AND masco_code ~ '^[0-9]{6}$')<>655
 THEN RAISE EXCEPTION 'MASCO STEM role identities were lost'; END IF;
 IF EXISTS(SELECT 1 FROM roles GROUP BY lower(btrim(role_title)) HAVING count(*)>1)
 OR EXISTS(SELECT 1 FROM roles GROUP BY masco_code HAVING count(*)>1)
 OR EXISTS(SELECT 1 FROM skill_taxonomy GROUP BY lower(btrim(canonical_name)) HAVING count(*)>1)
 THEN RAISE EXCEPTION 'Duplicate canonical roles/skills remain'; END IF;
 IF EXISTS(SELECT 1 FROM (SELECT skill_id,lower(btrim(canonical_name)) term FROM skill_taxonomy
    UNION SELECT skill_id,lower(btrim(alias)) FROM skill_aliases) x GROUP BY term HAVING count(DISTINCT skill_id)>1)
 THEN RAISE EXCEPTION 'Exact-term alias ambiguity remains'; END IF;
 IF EXISTS(SELECT 1 FROM role_skills r JOIN skill_taxonomy s USING(skill_id) WHERE r.skill_name<>s.canonical_name OR r.skill_type<>s.skill_type)
 THEN RAISE EXCEPTION 'Role-skill labels/types do not match taxonomy'; END IF;
 IF EXISTS(SELECT 1 FROM fix_mapping r WHERE r.approved AND NOT EXISTS(SELECT 1 FROM role_skills s WHERE s.role_id=r.role_id))
 OR EXISTS(SELECT 1 FROM role_skills s JOIN fix_mapping m USING(role_id) WHERE NOT m.approved)
 OR (SELECT count(*) FROM role_skills WHERE role_id='M232102')<>11
 THEN RAISE EXCEPTION 'Core candidate coverage regression'; END IF;
 SELECT md5(jsonb_build_object(
  'columns',(SELECT jsonb_agg(to_jsonb(c) ORDER BY table_name,ordinal_position) FROM information_schema.columns c WHERE table_schema='rerouteher'),
  'constraints',(SELECT jsonb_agg(jsonb_build_array(conrelid::regclass::text,conname,pg_get_constraintdef(oid),convalidated) ORDER BY conrelid::regclass::text,conname) FROM pg_constraint WHERE connamespace='rerouteher'::regnamespace),
  'indexes',(SELECT jsonb_agg(to_jsonb(i) ORDER BY tablename,indexname) FROM pg_indexes i WHERE schemaname='rerouteher'),
  'views',(SELECT jsonb_agg(to_jsonb(v) ORDER BY table_name) FROM information_schema.views v WHERE table_schema='rerouteher'),
  'triggers',(SELECT jsonb_agg(jsonb_build_array(tgrelid::regclass::text,tgname,pg_get_triggerdef(oid),tgenabled) ORDER BY tgrelid::regclass::text,tgname) FROM pg_trigger WHERE tgrelid IN (SELECT oid FROM pg_class WHERE relnamespace='rerouteher'::regnamespace) AND NOT tgisinternal)
 )::text) INTO schema_fp;
 IF schema_fp<>current_setting('quality_fix.schema_before') THEN RAISE EXCEPTION 'Permanent schema changed'; END IF;
END $verify$;

INSERT INTO dataset_metadata VALUES
('d13_quality_fix_20260830.policy',jsonb_build_object(
 'version','D13 MASCO2020 Core Candidates v1','test_only',true,'production_ready',false,
 'core_candidate_links',13147,'conditional_links_archived',22203,'low_confidence_essential_links_held',5674,
 'user_authorized_approval_threshold','medium','auto_approved_roles',442,'low_confidence_roles_pending',213,
 'esco_comparisons_preserved',true,'mapping_confidence_and_relation_not_upgraded',true,
 'not_a_validated_readiness_assessment',true,'alias_cache_restart_required',true,
 'remaining_backend_issues',jsonb_build_array('Shared-ESCO LIMIT 1 role lookup','Forced weak recommendations','Missing skill IDs','Empty-band score bias','Stale snapshots'),
 'legacy_group_roles_requiring_review',jsonb_build_array('R03','R04','R05','R07','R08','R09','R10'))),
('d13_quality_fix_20260830.alias_review',(SELECT coalesce(jsonb_agg(to_jsonb(x)),'[]'::jsonb) FROM fix_alias_remove x)),
('d13_quality_fix_20260830.role_merge_map',(SELECT jsonb_agg(to_jsonb(x)) FROM fix_role_map x)),
('d13_quality_fix_20260830.receipt',jsonb_build_object('applied_at',clock_timestamp(),
 'backup_path',current_setting('quality_fix.backup_path'),'backup_sha256',current_setting('quality_fix.backup_sha256'),
 'schema_signature',current_setting('quality_fix.schema_before'),'schema_changed',false,
 'roles',662,'masco2020_stem_roles',655,'role_skills',13266,'role_skill_lineage',13266,
 'skill_concepts',6121,'skill_ids_merged',0,'archived_alias_rows',(SELECT count(*) FROM fix_alias_remove),
 'historical_reference_rows_preserved',true));
INSERT INTO dataset_metadata(metadata_key,metadata_value)
SELECT 'd13_quality_fix_20260830.mapping.'||m.role_id,
 to_jsonb(m) || jsonb_build_object('reviewer','User-Authorized Automated Confidence Rule',
 'review_date','2026-08-30','use_in_role_skills',m.approved,'production_ready',false,
 'approval_is_not_exact_equivalence',true,'mapping_authority','Project-Derived Test Crosswalk',
 'source_mapping_metadata_key','d13_masco2020_rebuilt_20260830.mapping.'||m.role_id)
FROM fix_mapping m;
\if :fix_commit
COMMIT;
\echo DATA_QUALITY_FIX_COMMITTED
\else
ROLLBACK;
\echo REHEARSAL_PASSED_NO_DATABASE_CHANGES
\endif
