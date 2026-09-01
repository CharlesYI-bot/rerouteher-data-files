"""Build a data-only migration for the inspected, populated rerouteher_test.

No database is contacted by this builder. Requires the reviewed D13 release.
The generated psql script defaults to a ROLLBACK-only rehearsal.
"""
from pathlib import Path
import csv, gzip, hashlib, json, re

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent
OLD = PROJECT / 'ReRouteHer_D13_FINAL_2026-08-30'
NEW = PROJECT / 'ReRouteHer_D13_MASCO2020_2026-08-30'
PREFIX = 'd13_masco2020_rebuilt_20260830'
MIG = 'd13_masco2020_migration_20260830'
BACKUP = '/var/lib/postgresql/masco2020_migration_20260830.MLQhVm'
BACKUP_HASH = 'dc6c47767eb7bb533d20e30ffcdc34f71114dc23f1becd5da31cfa3d1ca6e3d7'
SCHEMA_HASH = '07cdc5de3a8721e6557717a407fad933968dffde541a441c993b6eacf1925ff1'
TABLES = ['roles','skill_taxonomy','skill_aliases','role_skills','role_skill_lineage','dataset_metadata']

def read(p):
    with p.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def lit(value):
    return "E'" + str(value).replace('\\','\\\\').replace("'","''").replace('\n','\\n').replace('\r','\\r') + "'"

def arr(values):
    return 'ARRAY[' + ','.join(lit(x) for x in sorted(values)) + ']::text[]'

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

SCHEMA_SQL = """SELECT md5(jsonb_build_object(
 'columns',(SELECT jsonb_agg(to_jsonb(c) ORDER BY table_name,ordinal_position) FROM information_schema.columns c WHERE table_schema='rerouteher'),
 'constraints',(SELECT jsonb_agg(jsonb_build_array(conrelid::regclass::text,conname,pg_get_constraintdef(oid),convalidated) ORDER BY conrelid::regclass::text,conname) FROM pg_constraint WHERE connamespace='rerouteher'::regnamespace),
 'indexes',(SELECT jsonb_agg(to_jsonb(i) ORDER BY tablename,indexname) FROM pg_indexes i WHERE schemaname='rerouteher'),
 'views',(SELECT jsonb_agg(to_jsonb(v) ORDER BY table_name) FROM information_schema.views v WHERE table_schema='rerouteher'),
 'triggers',(SELECT jsonb_agg(jsonb_build_array(tgrelid::regclass::text,tgname,pg_get_triggerdef(oid),tgenabled) ORDER BY tgrelid::regclass::text,tgname) FROM pg_trigger WHERE tgrelid IN (SELECT oid FROM pg_class WHERE relnamespace='rerouteher'::regnamespace) AND NOT tgisinternal)
 )::text)"""

def snapshot_sql(role_ids, skill_ids, after=False):
    meta_filter = f"WHERE NOT starts_with(metadata_key,{lit(PREFIX+'.')}) AND NOT starts_with(metadata_key,{lit(MIG+'.')})" if after else ''
    return f"""
DO $snapshot$
DECLARE t record; predicate text; fp jsonb; baseline jsonb := '{{}}'::jsonb;
        oldbaseline jsonb; schema_fp text;
BEGIN
 FOR t IN SELECT tablename FROM pg_tables WHERE schemaname='rerouteher' ORDER BY tablename LOOP
   predicate := CASE
     WHEN t.tablename IN ('roles','role_skills','role_skill_lineage') THEN 'WHERE NOT (role_id = ANY(' || {lit(arr(role_ids))} || '))'
     WHEN t.tablename IN ('skill_taxonomy','skill_aliases') THEN 'WHERE NOT (skill_id = ANY(' || {lit(arr(skill_ids))} || '))'
     WHEN t.tablename='dataset_metadata' THEN {lit(meta_filter)}
     ELSE '' END;
   EXECUTE format('SELECT jsonb_build_object(''rows'',count(*),''md5'',md5(coalesce(string_agg(md5(to_jsonb(z)::text),'''' ORDER BY md5(to_jsonb(z)::text)),''''))) FROM rerouteher.%I z %s',t.tablename,predicate) INTO fp;
   baseline := baseline || jsonb_build_object(t.tablename,fp);
 END LOOP;
 {SCHEMA_SQL} INTO schema_fp;
 {'''oldbaseline := current_setting('d13_migration.preserved_rows')::jsonb;
 IF baseline IS DISTINCT FROM oldbaseline THEN RAISE EXCEPTION 'Unrelated or original rows changed; rolling back entire migration'; END IF;
 IF schema_fp IS DISTINCT FROM current_setting('d13_migration.schema_fp') THEN RAISE EXCEPTION 'Schema signature changed; rolling back entire migration'; END IF;''' if after else '''PERFORM set_config('d13_migration.preserved_rows',baseline::text,true);
 PERFORM set_config('d13_migration.schema_fp',schema_fp,true);'''}
END $snapshot$;
"""

def main():
    assert len(BACKUP_HASH) == len(SCHEMA_HASH) == 64
    validation = json.loads((NEW/'02_QA/D13_validation_report.json').read_text())
    assert validation['result']=='PASS' and validation['checks_passed']==48
    source = NEW/'04_DATABASE/MASCO2020_LOAD_EMPTY_TEST_SCHEMA.sql'
    source_report = json.loads((NEW/'02_QA/sql_validation.json').read_text())
    assert digest(source)==source_report['sql_sha256']
    oldroles = {r['role_id'] for r in read(OLD/'00_SOURCE_SNAPSHOT/D11_STEM_roles.csv')}
    newroles = {r['role_id'] for r in read(NEW/'01_TABLES/D11_STEM_roles.csv')}
    oldskills = {r['skill_id'] for r in read(OLD/'01_TABLES/skill_taxonomy.csv')}
    newskills = {r['skill_id'] for r in read(NEW/'01_TABLES/skill_taxonomy.csv')}
    assert (len(oldroles),len(newroles),len(oldskills),len(newskills))==(657,655,6164,6080)
    statements = {t:[] for t in TABLES}
    counts = {t:0 for t in TABLES}
    # Generated source has one VALUES row per physical line, with all literal
    # newlines escaped. A terminating row ends with );, never a quoted literal.
    pending=[]; table=None
    for line in source.read_text().splitlines(keepends=True):
        m=re.match(r'INSERT INTO rerouteher\.(\w+)\s*\(',line)
        if m:
            assert not pending
            table=m[1]; assert table in statements
            pending=[line]
        elif pending:
            pending.append(line)
            if line.startswith('('): counts[table]+=1
            if line.rstrip().endswith(');'):
                statement=''.join(pending)
                if table in ('roles','skill_taxonomy'):
                    columns=re.search(r'\((.*?)\) VALUES',statement.splitlines()[0]).group(1).replace(' ','').split(',')
                    key='role_id' if table=='roles' else 'skill_id'
                    statement=statement.rstrip()[:-1]+f' ON CONFLICT ({key}) DO UPDATE SET '+', '.join(c+'=EXCLUDED.'+c for c in columns if c!=key)+';\n'
                statements[table].append(statement); pending=[];table=None
    assert not pending
    assert counts==dict(roles=655,skill_taxonomy=6080,skill_aliases=37654,role_skills=41024,role_skill_lineage=41024,dataset_metadata=8068),counts
    oldr, newr, olds, news = arr(oldroles),arr(newroles),arr(oldskills),arr(newskills)
    expected_total={'roles':665,'skill_taxonomy':6121,'skill_aliases':37730,'role_skills':41194,'role_skill_lineage':41194}
    old_totals={'roles':667,'skill_taxonomy':6205,'skill_aliases':38285,'role_skills':41118,'role_skill_lineage':41118}
    before_counts='\n'.join(f"IF (SELECT count(*) FROM rerouteher.{t})<>{n} THEN RAISE EXCEPTION 'Baseline {t} count changed; inspect before retrying'; END IF;" for t,n in old_totals.items())
    after_counts='\n'.join(f"IF (SELECT count(*) FROM rerouteher.{t})<>{n} THEN RAISE EXCEPTION 'Unexpected final {t} count'; END IF;" for t,n in expected_total.items())
    sql=f"""-- DATA-ONLY replacement of the previous D13 test release, not a schema import.
-- Target: rerouteher_test in postgresql-database-wxnjpd2ia8avtwbs739mtamk.
-- Original R01-R10 and all unrelated rows must remain byte/value identical.
-- Run with psql. Default is a complete ROLLBACK-only rehearsal.
-- Commit only after approval: psql -v d13_dry_run=false -f THIS_FILE
\\set ON_ERROR_STOP on
\\if :{{?d13_dry_run}}
\\else
\\set d13_dry_run true
\\endif
BEGIN;
SET LOCAL lock_timeout='15s';
SET LOCAL statement_timeout='5min';
SET LOCAL standard_conforming_strings=on;
SET LOCAL application_name='rerouteher_masco2020_data_migration';
DO $guard$
DECLARE t record; n bigint; expected_role_ids text[] := {oldr};
        expected_skill_ids text[] := {olds}; ref_ids text[];
BEGIN
 IF current_database()<>'rerouteher_test' THEN RAISE EXCEPTION 'Wrong database'; END IF;
 IF NOT pg_try_advisory_xact_lock(hashtext('{MIG}')) THEN RAISE EXCEPTION 'Another MASCO 2020 migration is running'; END IF;
 FOR t IN SELECT tablename FROM pg_tables WHERE schemaname='rerouteher' ORDER BY tablename LOOP
   EXECUTE format('LOCK TABLE rerouteher.%I IN SHARE ROW EXCLUSIVE MODE',t.tablename);
 END LOOP;
 IF (SELECT count(*) FROM pg_tables WHERE schemaname='rerouteher')<>35 THEN RAISE EXCEPTION 'Expected original 35-table schema; inspect before retrying'; END IF;
 {before_counts}
 IF (SELECT count(*) FROM rerouteher.roles WHERE role_id=ANY(expected_role_ids))<>657 THEN RAISE EXCEPTION 'Expected exact 657 prior D13 role IDs'; END IF;
 IF (SELECT count(*) FROM rerouteher.skill_taxonomy WHERE skill_id=ANY(expected_skill_ids))<>6164 THEN RAISE EXCEPTION 'Expected exact prior D13 skill IDs'; END IF;
 IF (SELECT count(*) FROM rerouteher.roles WHERE role_id=ANY(ARRAY['R01','R02','R03','R04','R05','R06','R07','R08','R09','R10']))<>10 THEN RAISE EXCEPTION 'Original ten role IDs changed'; END IF;
 IF EXISTS(SELECT 1 FROM rerouteher.roles WHERE role_id=ANY({newr}) AND NOT role_id=ANY(expected_role_ids)) THEN RAISE EXCEPTION 'New role ID collides with unrelated row'; END IF;
 IF EXISTS(SELECT 1 FROM rerouteher.skill_taxonomy WHERE skill_id=ANY({news}) AND NOT skill_id=ANY(expected_skill_ids)) THEN RAISE EXCEPTION 'New skill ID collides with unrelated row'; END IF;
 IF (SELECT count(*) FROM rerouteher.dataset_metadata WHERE starts_with(metadata_key,'d13_test_20260830.'))<>6822 THEN RAISE EXCEPTION 'Previous import metadata changed'; END IF;
 IF EXISTS(SELECT 1 FROM rerouteher.dataset_metadata WHERE starts_with(metadata_key,'{PREFIX}.') OR starts_with(metadata_key,'{MIG}.')) THEN RAISE EXCEPTION 'This migration/release already exists; do not repeat'; END IF;
 IF (SELECT count(*) FROM rerouteher.role_skills WHERE role_id=ANY(expected_role_ids))<>40948 OR (SELECT count(*) FROM rerouteher.role_skill_lineage WHERE role_id=ANY(expected_role_ids))<>40948 THEN RAISE EXCEPTION 'Prior project link counts changed'; END IF;
 IF (SELECT count(*) FROM rerouteher.skill_aliases WHERE skill_id=ANY(expected_skill_ids))<>38209 THEN RAISE EXCEPTION 'Prior project alias count changed'; END IF;
 IF EXISTS(SELECT 1 FROM rerouteher.role_skills WHERE skill_id=ANY(expected_skill_ids) AND NOT role_id=ANY(expected_role_ids)) OR EXISTS(SELECT 1 FROM rerouteher.role_skill_lineage WHERE skill_id=ANY(expected_skill_ids) AND NOT role_id=ANY(expected_role_ids)) THEN RAISE EXCEPTION 'Prior ESCO skills are now shared with unrelated roles'; END IF;
 IF EXISTS(SELECT 1 FROM pg_trigger WHERE NOT tgisinternal AND tgrelid IN ('rerouteher.roles'::regclass,'rerouteher.skill_taxonomy'::regclass,'rerouteher.skill_aliases'::regclass,'rerouteher.role_skills'::regclass,'rerouteher.role_skill_lineage'::regclass)) THEN RAISE EXCEPTION 'Unreviewed user trigger on a target table'; END IF;
 FOR t IN SELECT c.table_schema,c.table_name,c.column_name FROM information_schema.columns c JOIN information_schema.tables b USING(table_schema,table_name)
   WHERE b.table_type='BASE TABLE' AND c.table_schema NOT IN ('pg_catalog','information_schema') AND c.column_name IN ('role_id','skill_id')
   AND NOT (c.table_schema='rerouteher' AND c.table_name IN ('roles','skill_taxonomy','role_skills','role_skill_lineage','skill_aliases')) LOOP
   ref_ids := CASE WHEN t.column_name='role_id' THEN expected_role_ids || {newr} ELSE expected_skill_ids || {news} END;
   EXECUTE format('SELECT count(*) FROM %I.%I WHERE %I=ANY($1)',t.table_schema,t.table_name,t.column_name) INTO n USING ref_ids;
   IF n<>0 THEN RAISE EXCEPTION 'Unreviewed dependent rows in %.%.%: %',t.table_schema,t.table_name,t.column_name,n; END IF;
 END LOOP;
END $guard$;
"""
    sql+=snapshot_sql(oldroles,oldskills)
    sql+=f"""
-- Preserve old role identities before any code is reused. Previous mapping
-- metadata and original ESCO comparisons remain unchanged as historical data.
INSERT INTO rerouteher.dataset_metadata(metadata_key,metadata_value)
SELECT '{MIG}.prior_role.'||role_id,to_jsonb(r) FROM rerouteher.roles r WHERE role_id=ANY({oldr});
DELETE FROM rerouteher.role_skill_lineage WHERE role_id=ANY({oldr});
DELETE FROM rerouteher.role_skills WHERE role_id=ANY({oldr});
DELETE FROM rerouteher.skill_aliases WHERE skill_id=ANY({olds});
DELETE FROM rerouteher.roles WHERE role_id=ANY({oldr}) AND NOT role_id=ANY({newr});
DELETE FROM rerouteher.skill_taxonomy WHERE skill_id=ANY({olds}) AND NOT skill_id=ANY({news});
"""
    for tab in TABLES:
        sql+=f'\n-- New D13 {tab}: {counts[tab]} input rows\n'+''.join(statements[tab])
    sql+=f"""
UPDATE rerouteher.dataset_metadata SET metadata_value=metadata_value || '{{"sql_target_database":"rerouteher_test","prior_release_migration":true,"import_requires_empty_data_tables":false,"live_database_modified":true}}'::jsonb WHERE metadata_key='{PREFIX}.release';
DO $verify$
BEGIN
 {after_counts}
 IF (SELECT count(*) FROM rerouteher.roles WHERE role_id=ANY({newr}))<>655 THEN RAISE EXCEPTION 'New role scope incomplete'; END IF;
 IF (SELECT count(*) FROM rerouteher.skill_taxonomy WHERE skill_id=ANY({news}))<>6080 THEN RAISE EXCEPTION 'New skill scope incomplete'; END IF;
 IF EXISTS(SELECT 1 FROM rerouteher.roles WHERE role_id=ANY({newr}) AND (masco_code !~ '^[0-9]{{6}}$' OR role_id<>'M'||masco_code OR vector_dims(role_embedding)<>384 OR abs(vector_norm(role_embedding)-1)>0.00001)) THEN RAISE EXCEPTION 'Invalid role identity/vector'; END IF;
 IF EXISTS(SELECT 1 FROM rerouteher.skill_taxonomy WHERE skill_id=ANY({news}) AND (vector_dims(embedding)<>384 OR abs(vector_norm(embedding)-1)>0.00001)) THEN RAISE EXCEPTION 'Invalid skill vector'; END IF;
 IF EXISTS(SELECT 1 FROM rerouteher.role_skills s JOIN rerouteher.skill_taxonomy t USING(skill_id) JOIN rerouteher.roles r USING(role_id) WHERE s.role_id=ANY({newr}) AND (s.skill_name<>t.canonical_name OR s.skill_type<>t.skill_type OR s.source_occupation_code<>r.esco_code OR s.importance NOT IN (50,100))) THEN RAISE EXCEPTION 'Inconsistent D13 skill join'; END IF;
 IF (SELECT count(DISTINCT role_id) FROM rerouteher.role_skills WHERE role_id=ANY({newr}))<>655 THEN RAISE EXCEPTION 'Some new roles have no skill links'; END IF;
 IF EXISTS(SELECT 1 FROM rerouteher.skill_aliases WHERE skill_id=ANY({news}) AND alias<>lower(alias)) THEN RAISE EXCEPTION 'Matching aliases must be lowercase'; END IF;
 IF EXISTS(SELECT 1 FROM rerouteher.roles r JOIN rerouteher.dataset_metadata m ON m.metadata_key='{PREFIX}.mapping.'||r.role_id WHERE r.role_id=ANY({newr}) AND r.esco_code<>m.metadata_value->>'chosen_esco_code') THEN RAISE EXCEPTION 'ESCO coverage code mismatch'; END IF;
 IF (SELECT count(*) FROM rerouteher.dataset_metadata WHERE starts_with(metadata_key,'{PREFIX}.'))<>8068 THEN RAISE EXCEPTION 'New metadata count mismatch'; END IF;
 IF (SELECT count(*) FROM rerouteher.dataset_metadata WHERE starts_with(metadata_key,'{PREFIX}.source_esco.'))<>657 THEN RAISE EXCEPTION 'Original ESCO comparison scope missing'; END IF;
 IF EXISTS(SELECT 1 FROM rerouteher.roles WHERE role_id=ANY({arr(oldroles-newroles)})) OR EXISTS(SELECT 1 FROM rerouteher.skill_taxonomy WHERE skill_id=ANY({arr(oldskills-newskills)})) THEN RAISE EXCEPTION 'Superseded project records remain active'; END IF;
END $verify$;
"""
    sql+=snapshot_sql(newroles,newskills,after=True)
    receipt={'dataset':'D13 MASCO 2020 STEM rebuilt with Title Case','database':'rerouteher_test','source_sql_sha256':digest(source),'backup_directory':BACKUP,'backup_sha256':BACKUP_HASH,'schema_dump_sha256':SCHEMA_HASH,'old_project_roles':657,'new_project_roles':655,'original_roles_preserved':10,'deleted_superseded_role_ids':382,'new_role_ids':380,'old_only_skills_removed':130,'new_skill_ids':46,'schema_changed':False,'original_esco_comparison_records':657,'total_rows_after':expected_total,'test_only':True}
    sql+=f"""
INSERT INTO rerouteher.dataset_metadata(metadata_key,metadata_value) VALUES
('{MIG}.receipt',{lit(json.dumps(receipt,separators=(',',':')))}::jsonb || jsonb_build_object('committed_at',clock_timestamp(),'preserved_rows_baseline',current_setting('d13_migration.preserved_rows')::jsonb,'schema_signature',current_setting('d13_migration.schema_fp')));
DO $done$ BEGIN RAISE NOTICE 'All migration checks passed: 655 MASCO 2020 roles plus 10 original roles; original rows and schema unchanged'; END $done$;
\\if :d13_dry_run
ROLLBACK;
\\echo REHEARSAL_PASSED_NO_DATABASE_CHANGES
\\else
COMMIT;
\\echo MASCO2020_MIGRATION_COMMITTED
\\endif
"""
    assert not re.search(r'^\s*(CREATE|ALTER|DROP|TRUNCATE)\s',sql,re.M|re.I)
    assert 'CASCADE' not in sql
    assert sql.count('DELETE FROM rerouteher.')==5
    assert len(re.findall(r'^UPDATE rerouteher\.',sql,re.M))==1
    output=ROOT/'MASCO2020_UPDATE_EXISTING_TEST_DATABASE.sql'
    output.write_text(sql,encoding='utf-8')
    with (ROOT/(output.name+'.gz')).open('wb') as f:
        with gzip.GzipFile(filename='',mode='wb',fileobj=f,mtime=0) as gz:gz.write(sql.encode())
    checks={'status':'PREPARED_NOT_EXECUTED','source_checks_passed':48,'source_sql_sha256':digest(source),'migration_sql_sha256':digest(output),'gzip_sha256':digest(ROOT/(output.name+'.gz')),'sql_bytes':output.stat().st_size,'gzip_bytes':(ROOT/(output.name+'.gz')).stat().st_size,'input_counts':counts,'expected_after_counts':expected_total,'schema_ddl_statements':0,'delete_statements':5,'deletions_exactly_scoped_to_prior_project_ids':True,'default_behavior':'rehearsal with rollback','backup':receipt,'limitations':['SQL checks are structural, not a PostgreSQL execution test.','Computer Use action-time approval is still required before replacement/deletion.']}
    (ROOT/'migration_validation.json').write_text(json.dumps(checks,indent=2)+'\n')
    print(json.dumps(checks,indent=2))

if __name__=='__main__': main()
