from pathlib import Path
import csv, re, hashlib

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
ORIGINAL = ROOT / 'ReRouteHer_Skill_SQL_Review_2026-08-30/originals'
PREFIX = 'skill_bands_fix_20260831'

def quote(s):
    return "'" + s.replace("'", "''") + "'"

noise = list(csv.DictReader((ROOT / 'ReRouteHer_Skill_SQL_Review_2026-08-30/cleanup_candidate_preview.csv').open()))
noise_values = ',\n'.join('('+','.join(map(quote,(r['role_id'],r['skill_ids'],r['skill_name'])))+')' for r in noise)
ai = (ORIGINAL/'ai-usage-band.sql').read_text()
soft = (ORIGINAL/'soft-band.sql').read_text()
ai_master = ai[ai.index('INSERT INTO rerouteher.skill_taxonomy'):ai.index('-- PART C:')]
ai_master = ai_master[:ai_master.index(';')+1].replace('rerouteher.skill_taxonomy','_ai_master')
ai_master = ai_master.replace('DigComp 2.2 (AI literacy)','ReRouteHer curated AI usage; inspired by DigComp 2.2')
soft_inserts = soft[soft.index('INSERT INTO rerouteher.role_skills'):soft.index('COMMIT;')]
soft_inserts = soft_inserts.replace('INSERT INTO rerouteher.role_skills','INSERT INTO _desired')
ai_inserts = ai[ai.index('INSERT INTO rerouteher.role_skills'):ai.index('COMMIT;')]
ai_inserts = ai_inserts.replace('INSERT INTO rerouteher.role_skills','INSERT INTO _desired')
ai_inserts = ai_inserts.replace('FROM rerouteher.role_skills rs\n  WHERE rs.role_id = r.role_id AND rs.skill_name', 'FROM _evidence rs\n  WHERE rs.role_id = r.role_id AND rs.skill_name')
# Avoid treating any software use as software development, and generic design
# (e.g. database design) as visual-content work. Preserve the other domain rules.
ai_inserts = ai_inserts.replace('(computer programming|software|debug|scripting|web programming|software librar|design pattern)', '(computer programming|software develop|develop.{0,30}software|debug|scripting|web programming|software librar|design pattern)')
ai_inserts = ai_inserts.replace('(design|graphic|cad|technical drawing|visual|animation|multimedia|creative suite)', '(graphic|cad|technical drawing|visual content|visual design|animation|multimedia|creative suite|design.{0,20}(image|layout|visual|graphic)|image edit)')

head = r"""-- Corrected execution of the three user-supplied scripts. Database only.
-- Keep digital taxonomy; allow ai_usage separately. Preserve original soft rules.
-- Cleanup list explicitly authorized by user; not independently occupationally validated.
-- All active-row changes have before/after images in dataset_metadata.
BEGIN;
SET LOCAL search_path=rerouteher,public;
SET LOCAL lock_timeout='5s';
SET LOCAL statement_timeout='90s';
SET LOCAL idle_in_transaction_session_timeout='120s';
DO $guard$ BEGIN
 IF current_database()<>'rerouteher_test' THEN RAISE EXCEPTION 'Wrong database: %',current_database(); END IF;
END $guard$;
LOCK TABLE rerouteher.roles IN SHARE MODE;
LOCK TABLE rerouteher.skill_taxonomy,rerouteher.role_skills,rerouteher.role_skill_lineage,rerouteher.digital_skill_rating_lineage,rerouteher.dataset_metadata IN SHARE ROW EXCLUSIVE MODE;
CREATE TEMP TABLE _before_role_skills ON COMMIT DROP AS TABLE rerouteher.role_skills;
CREATE TEMP TABLE _before_role_skill_lineage ON COMMIT DROP AS TABLE rerouteher.role_skill_lineage;
CREATE TEMP TABLE _before_digital_skill_rating_lineage ON COMMIT DROP AS TABLE rerouteher.digital_skill_rating_lineage;
CREATE TEMP TABLE _before_skill_taxonomy ON COMMIT DROP AS TABLE rerouteher.skill_taxonomy;
CREATE TEMP TABLE _before_constraints ON COMMIT DROP AS
 SELECT conrelid::regclass::text AS tbl,conname,pg_get_constraintdef(oid) AS definition
 FROM pg_constraint WHERE conrelid IN ('rerouteher.role_skills'::regclass,'rerouteher.skill_taxonomy'::regclass)
 AND conname IN ('role_skills_skill_type_check','skill_taxonomy_skill_type_check');
CREATE TEMP TABLE _noise_list(role_id text,skill_id text,skill_name text,PRIMARY KEY(role_id,skill_id)) ON COMMIT DROP;
INSERT INTO _noise_list VALUES
""" + noise_values + r""";
CREATE TEMP TABLE _noise ON COMMIT DROP AS
 SELECT rs.* FROM rerouteher.role_skills rs JOIN _noise_list n USING(role_id,skill_id,skill_name)
 WHERE rs.source IS DISTINCT FROM 'curated';
-- Fixed, pre-addition evidence, excluding the cleanup candidates and generated bands.
CREATE TEMP TABLE _evidence ON COMMIT DROP AS
 SELECT rs.* FROM rerouteher.role_skills rs
 WHERE rs.skill_type IN ('technical','digital') AND rs.source IS DISTINCT FROM 'curated'
 AND NOT starts_with(rs.skill_id,'AIUSE_')
 AND NOT EXISTS(SELECT 1 FROM _noise n WHERE (n.role_id,n.skill_id)=(rs.role_id,rs.skill_id));
CREATE TEMP TABLE _ai_master (LIKE rerouteher.skill_taxonomy INCLUDING DEFAULTS) ON COMMIT DROP;
""" + ai_master + r"""
CREATE TEMP TABLE _desired (LIKE rerouteher.role_skills INCLUDING DEFAULTS) ON COMMIT DROP;
ALTER TABLE _desired ADD PRIMARY KEY(role_id,skill_id);
ALTER TABLE _desired ALTER COLUMN importance_method SET DEFAULT 'curated_soft_rule_v1: universal=70; relevance=60; project assumption, not O*NET occupational rating';
""" + soft_inserts + r"""
ALTER TABLE _desired ALTER COLUMN importance_method SET DEFAULT 'curated_ai_exposure_rule_v1: high=80; medium=60; low=40';
""" + ai_inserts + r"""
UPDATE _desired d SET curation_note=coalesce(d.curation_note,'') ||
 CASE WHEN starts_with(d.skill_id,'AIUSE_') THEN '; skill_bands_fix_20260831; domain evidence excludes generated skills and approved cleanup'
 ELSE '; skill_bands_fix_20260831; user-authorized test mapping; not an O*NET occupational rating' END;

DO $precheck$ BEGIN
 IF (SELECT count(*) FROM _noise_list)<>124 THEN RAISE EXCEPTION 'Cleanup list changed'; END IF;
 IF EXISTS(SELECT 1 FROM _noise_list n JOIN rerouteher.role_skills r USING(role_id,skill_id) WHERE n.skill_name<>r.skill_name) THEN RAISE EXCEPTION 'Cleanup label changed'; END IF;
 IF EXISTS(SELECT 1 FROM _desired d LEFT JOIN rerouteher.skill_taxonomy t USING(skill_id) LEFT JOIN _ai_master a USING(skill_id) WHERE t.skill_id IS NULL AND a.skill_id IS NULL) THEN RAISE EXCEPTION 'Missing master skill'; END IF;
 IF EXISTS(SELECT 1 FROM _ai_master a JOIN rerouteher.skill_taxonomy t USING(skill_id) WHERE a.canonical_name<>t.canonical_name OR a.embedding_model<>t.embedding_model OR a.definition IS DISTINCT FROM t.definition OR a.embedding::text<>t.embedding::text OR t.skill_type<>'ai_usage') THEN RAISE EXCEPTION 'Conflicting existing AI master'; END IF;
 IF EXISTS(SELECT 1 FROM rerouteher.role_skills r JOIN rerouteher.skill_taxonomy t USING(skill_id) WHERE r.skill_type<>t.skill_type OR r.skill_name<>t.canonical_name) THEN RAISE EXCEPTION 'Preexisting taxonomy mismatch'; END IF;
 IF EXISTS(SELECT 1 FROM rerouteher.role_skill_lineage l FULL JOIN rerouteher.role_skills r USING(role_id,skill_id) WHERE l.role_id IS NULL OR r.role_id IS NULL) THEN RAISE EXCEPTION 'Preexisting lineage mismatch'; END IF;
 RAISE NOTICE 'PLAN %',jsonb_build_object('database',current_database(),'roles',(SELECT count(*) FROM roles),'cleanup',(SELECT count(*) FROM _noise),'new_soft_script_links',(SELECT count(*) FROM _desired WHERE NOT starts_with(skill_id,'AIUSE_')),'new_ai_links',(SELECT count(*) FROM _desired WHERE starts_with(skill_id,'AIUSE_')));
END $precheck$;

-- Widen only the two observed skill-type checks; preserve all other constraints.
DO $constraints$ DECLARE x record; actual text; BEGIN
 FOR x IN SELECT * FROM (VALUES ('skill_taxonomy','skill_taxonomy_skill_type_check'),('role_skills','role_skills_skill_type_check')) v(tbl,con) LOOP
  SELECT pg_get_constraintdef(oid) INTO STRICT actual FROM pg_constraint
  WHERE conrelid=format('rerouteher.%I',x.tbl)::regclass AND conname=x.con;
  IF actual NOT IN (
   'CHECK ((skill_type = ANY (ARRAY[''technical''::text, ''soft''::text, ''digital''::text])))',
   'CHECK ((skill_type = ANY (ARRAY[''technical''::text, ''soft''::text, ''digital''::text, ''ai_usage''::text])))'
  ) THEN RAISE EXCEPTION 'Unexpected constraint %: %',x.con,actual; END IF;
  IF position('ai_usage' IN actual)=0 THEN
   EXECUTE format('ALTER TABLE rerouteher.%I DROP CONSTRAINT %I',x.tbl,x.con);
   EXECUTE format('ALTER TABLE rerouteher.%I ADD CONSTRAINT %I CHECK (skill_type IN (''technical'',''soft'',''digital'',''ai_usage''))',x.tbl,x.con);
  END IF;
 END LOOP;
END $constraints$;

CREATE OR REPLACE FUNCTION pg_temp.apply_skill_bands() RETURNS void LANGUAGE plpgsql AS $apply$
DECLARE removed bigint; inserted bigint; BEGIN
 INSERT INTO rerouteher.skill_taxonomy SELECT * FROM _ai_master ON CONFLICT(skill_id) DO NOTHING;
 UPDATE rerouteher.skill_taxonomy SET skill_type='soft'
 WHERE skill_id IN ('ONET_2_A_1_b','ONET_2_A_1_d') AND skill_type<>'soft';
 DELETE FROM rerouteher.digital_skill_rating_lineage l USING _noise n WHERE (l.role_id,l.skill_id)=(n.role_id,n.skill_id);
 DELETE FROM rerouteher.role_skill_lineage l USING _noise n WHERE (l.role_id,l.skill_id)=(n.role_id,n.skill_id);
 DELETE FROM rerouteher.role_skills r USING _noise n WHERE (r.role_id,r.skill_id)=(n.role_id,n.skill_id) AND r.source IS DISTINCT FROM 'curated';
 GET DIAGNOSTICS removed=ROW_COUNT;
 UPDATE rerouteher.role_skills r SET skill_type=t.skill_type,skill_name=t.canonical_name FROM rerouteher.skill_taxonomy t
 WHERE r.skill_id=t.skill_id AND t.skill_id IN ('ONET_2_A_1_b','ONET_2_A_1_d') AND (r.skill_type<>t.skill_type OR r.skill_name<>t.canonical_name);
 INSERT INTO rerouteher.role_skills(role_id,skill_id,skill_name,skill_type,importance,source,source_occupation_code,source_element_id,importance_method,curation_note)
 SELECT d.role_id,d.skill_id,t.canonical_name,t.skill_type,d.importance,d.source,d.source_occupation_code,d.skill_id,d.importance_method,d.curation_note
 FROM _desired d JOIN rerouteher.skill_taxonomy t USING(skill_id)
 ON CONFLICT(role_id,skill_id) DO NOTHING;
 GET DIAGNOSTICS inserted=ROW_COUNT;
 UPDATE rerouteher.role_skill_lineage l SET skill_type=r.skill_type,skill_name=r.skill_name
 FROM rerouteher.role_skills r WHERE (l.role_id,l.skill_id)=(r.role_id,r.skill_id)
 AND r.skill_id IN ('ONET_2_A_1_b','ONET_2_A_1_d') AND (l.skill_type<>r.skill_type OR l.skill_name<>r.skill_name);
 INSERT INTO rerouteher.role_skill_lineage(role_id,skill_id,skill_name,skill_type,importance,source,source_occupation_code,source_element_id,importance_method,curation_note,raw_source_value,normalisation_or_rating_rule,one_line_justification,source_url,review_status)
 SELECT r.role_id,r.skill_id,r.skill_name,r.skill_type,r.importance,r.source,r.source_occupation_code,r.source_element_id,r.importance_method,r.curation_note,
 r.importance::text,r.importance_method,r.curation_note,NULL,'user_authorized_test_mapping'
 FROM rerouteher.role_skills r JOIN _desired d USING(role_id,skill_id) ON CONFLICT(role_id,skill_id) DO NOTHING;
 RAISE NOTICE 'APPLY inserted=% removed=%',inserted,removed;
END $apply$;
SELECT pg_temp.apply_skill_bands();

CREATE TEMP TABLE _first_pass_hash(table_name text PRIMARY KEY,hash text) ON COMMIT DROP;
DO $hash$ DECLARE t text; h text; BEGIN
 FOREACH t IN ARRAY ARRAY['role_skills','role_skill_lineage','digital_skill_rating_lineage','skill_taxonomy'] LOOP
 EXECUTE format('SELECT md5(coalesce(string_agg(md5(to_jsonb(x)::text),'''' ORDER BY md5(to_jsonb(x)::text)),'''')) FROM rerouteher.%I x',t) INTO h;
 INSERT INTO _first_pass_hash VALUES(t,h);
 END LOOP;
END $hash$;
-- Meaningful rerun test against already-mutated tables, within the same transaction.
SELECT pg_temp.apply_skill_bands();
DO $verify$ DECLARE x record; h text; BEGIN
 FOR x IN SELECT * FROM _first_pass_hash LOOP
 EXECUTE format('SELECT md5(coalesce(string_agg(md5(to_jsonb(t)::text),'''' ORDER BY md5(to_jsonb(t)::text)),'''')) FROM rerouteher.%I t',x.table_name) INTO h;
 IF h<>x.hash THEN RAISE EXCEPTION 'Rerun changed %',x.table_name; END IF;
 END LOOP;
 IF EXISTS(SELECT 1 FROM rerouteher.role_skills r JOIN rerouteher.skill_taxonomy t USING(skill_id) WHERE r.skill_name<>t.canonical_name OR r.skill_type<>t.skill_type) THEN RAISE EXCEPTION 'Master mismatch'; END IF;
 IF EXISTS(SELECT 1 FROM rerouteher.role_skills r FULL JOIN rerouteher.role_skill_lineage l USING(role_id,skill_id) WHERE r.role_id IS NULL OR l.role_id IS NULL OR r.skill_name<>l.skill_name OR r.skill_type<>l.skill_type OR r.importance IS DISTINCT FROM l.importance) THEN RAISE EXCEPTION 'Lineage mismatch'; END IF;
 IF EXISTS(SELECT 1 FROM _noise n JOIN rerouteher.role_skills r USING(role_id,skill_id)) THEN RAISE EXCEPTION 'Cleanup incomplete'; END IF;
 IF EXISTS(SELECT 1 FROM rerouteher.roles r CROSS JOIN (VALUES ('AIUSE_01'),('AIUSE_02'),('ONET_2_B_1_b'),('ONET_2_B_5_a'),('ONET_2_A_1_b'),('ONET_2_A_1_d'),('ONET_2_B_1_a'),('ONET_2_B_1_f'),('ONET_2_B_2_i'),('ONET_2_B_4_e'),('ONET_2_A_2_d'),('ONET_2_A_2_c')) s(id) LEFT JOIN rerouteher.role_skills rs ON rs.role_id=r.role_id AND rs.skill_id=s.id WHERE rs.skill_id IS NULL) THEN RAISE EXCEPTION 'Universal coverage incomplete'; END IF;
 IF EXISTS(SELECT 1 FROM _desired d LEFT JOIN rerouteher.role_skills r USING(role_id,skill_id) WHERE r.role_id IS NULL) THEN RAISE EXCEPTION 'Missing desired mapping'; END IF;
 IF EXISTS(SELECT 1 FROM _before_role_skills b LEFT JOIN rerouteher.role_skills r USING(role_id,skill_id) WHERE NOT EXISTS(SELECT 1 FROM _noise n WHERE (n.role_id,n.skill_id)=(b.role_id,b.skill_id)) AND b.skill_id NOT IN ('ONET_2_A_1_b','ONET_2_A_1_d') AND to_jsonb(b) IS DISTINCT FROM to_jsonb(r)) THEN RAISE EXCEPTION 'Unrelated role-skill changed'; END IF;
 IF EXISTS(SELECT 1 FROM _before_skill_taxonomy b LEFT JOIN rerouteher.skill_taxonomy t USING(skill_id) WHERE b.skill_id NOT IN ('ONET_2_A_1_b','ONET_2_A_1_d') AND to_jsonb(b) IS DISTINCT FROM to_jsonb(t)) THEN RAISE EXCEPTION 'Unrelated master changed'; END IF;
 RAISE NOTICE 'VALIDATION PASS: rerun stable, canonical names/types consistent, lineage matched, cleanup exact, required coverage complete, unrelated existing mappings preserved';
END $verify$;

-- Archive only changed/removed/inserted rows, retaining full recoverable images.
DO $archive$ DECLARE t text; keys text; before_rows jsonb; after_rows jsonb; BEGIN
 FOREACH t IN ARRAY ARRAY['role_skills','role_skill_lineage','digital_skill_rating_lineage','skill_taxonomy'] LOOP
 keys:=CASE WHEN t='skill_taxonomy' THEN 'skill_id' ELSE 'role_id,skill_id' END;
 EXECUTE format('SELECT coalesce(jsonb_agg(to_jsonb(b)),''[]''::jsonb) FROM pg_temp.%I b LEFT JOIN rerouteher.%I a USING(%s) WHERE to_jsonb(b) IS DISTINCT FROM to_jsonb(a)','_before_'||t,t,keys) INTO before_rows;
 EXECUTE format('SELECT coalesce(jsonb_agg(to_jsonb(a)),''[]''::jsonb) FROM rerouteher.%I a LEFT JOIN pg_temp.%I b USING(%s) WHERE to_jsonb(b) IS DISTINCT FROM to_jsonb(a)',t,'_before_'||t,keys) INTO after_rows;
 INSERT INTO rerouteher.dataset_metadata VALUES('skill_bands_fix_20260831.'||t,jsonb_build_object('before',before_rows,'after',after_rows)) ON CONFLICT(metadata_key) DO NOTHING;
 RAISE NOTICE 'ARCHIVE % before=% after=%',t,jsonb_array_length(before_rows),jsonb_array_length(after_rows);
 END LOOP;
 INSERT INTO rerouteher.dataset_metadata SELECT 'skill_bands_fix_20260831.constraints',jsonb_agg(to_jsonb(c)) FROM _before_constraints c ON CONFLICT(metadata_key) DO NOTHING;
END $archive$;
INSERT INTO rerouteher.dataset_metadata VALUES('skill_bands_fix_20260831.receipt',jsonb_build_object(
 'database',current_database(),'applied_at',clock_timestamp(),'roles',(SELECT count(*) FROM roles),'skill_taxonomy',(SELECT count(*) FROM skill_taxonomy),
 'role_skills',(SELECT count(*) FROM role_skills),'role_skill_lineage',(SELECT count(*) FROM role_skill_lineage),
 'removed_links',(SELECT count(*) FROM _noise),'inserted_links',(SELECT count(*) FROM _desired),
 'band_counts',(SELECT jsonb_object_agg(skill_type,n) FROM (SELECT skill_type,count(*) n FROM role_skills GROUP BY skill_type) b),
 'table_hashes',(SELECT jsonb_object_agg(table_name,hash) FROM _first_pass_hash),
 'scope','Database only; no application changes; user-authorized original soft policies and cleanup; fixed AI domain evidence',
 'user_backup','User reports duplicate database backup; not independently restored',
 'validation','passed including in-transaction rerun stability'
)) ON CONFLICT(metadata_key) DO NOTHING;
DO $report$ DECLARE x record; BEGIN
 RAISE NOTICE 'RECEIPT %',(SELECT metadata_value FROM dataset_metadata WHERE metadata_key='skill_bands_fix_20260831.receipt');
 FOR x IN SELECT skill_id,skill_name,count(*) n FROM role_skills WHERE starts_with(skill_id,'AIUSE_') GROUP BY 1,2 ORDER BY 1 LOOP RAISE NOTICE 'AI_COVERAGE %',row_to_json(x); END LOOP;
END $report$;
"""

(OUT/'REHEARSE.sql').write_text(head+'\nROLLBACK;\n')
(OUT/'APPLY.sql').write_text(head+'\nCOMMIT;\n')
(OUT/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256((OUT/n).read_bytes()).hexdigest()+'  '+n+'\n' for n in ['APPLY.sql','REHEARSE.sql']))
print('Generated APPLY.sql and REHEARSE.sql:',len(head),'characters; exact cleanup pairs:',len(noise))
