"""Promote the reviewed data-only draft for the user's database-update request.

Does not contact PostgreSQL. The source dataset and original draft are immutable.
The live command must supply explicit data-only limitation acknowledgement;
it does not pretend that the unchanged backend has been validated or fixed.
"""
from pathlib import Path
import csv
import gzip
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parent
DATA = ROOT.parent / 'ReRouteHer_Data_Quality_Fix_2026-08-30'


def read(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def main():
    source = DATA / '03_DATABASE_DRAFT/DATA_QUALITY_FIX.sql'
    sql = source.read_text()
    assert hashlib.sha256(sql.encode()).hexdigest() == '9cc500189c7e23c6e6da34933ed543389ba0732c84b97fff50984aba824ea996'
    assert json.loads((DATA / '02_QA/regression_results.json').read_text())['status'] == 'PASS'
    sql = sql.replace('-- HOLD LIVE COMMIT: core-only data exposes the deployed empty-band scoring bug.\n'
                      '-- Also requires tested backend compatibility: -v backend_compatibility_confirmed=true',
                      '-- USER-REQUESTED DATA-ONLY UPDATE. Backend remains unchanged and scores are not calibrated.\n'
                      '-- Commit requires action-time confirmation and -v data_only_limitations_acknowledged=true.')
    sql = sql.replace('backend_compatibility_confirmed', 'data_only_limitations_acknowledged')
    sql = sql.replace('STOP: fix and test role resolution, skill IDs, and empty-band scoring before activating this data',
                      'STOP: confirm data-only activation with known role-resolution, cache and scoring limitations')
    # Keep review status aligned with the corrected lineage export. Archive the
    # original active lineage too, as its user-authorized status will change.
    anchor = "     pred := 'z.role_id IN (SELECT old_id FROM fix_role_map) OR z.role_id IN (SELECT role_id FROM fix_mapping WHERE NOT approved) OR (z.role_id ~ ''^M[0-9]{6}$'' AND z.importance=50) OR z.skill_id IN (SELECT skill_id FROM fix_skill_patch)';"
    assert sql.count(anchor) == 1
    sql = sql.replace(anchor, anchor + "\n     IF t.tablename='role_skill_lineage' THEN pred := pred || ' OR z.role_id IN (SELECT role_id FROM fix_mapping)'; END IF;")
    anchor = "   ELSIF t.tablename='dataset_metadata' THEN"
    sql = sql.replace(anchor, """     IF t.tablename='role_skill_lineage' THEN
       expected_query := 'SELECT q.j || coalesce((SELECT jsonb_build_object(''review_status'',m.review_status) FROM fix_mapping m WHERE m.role_id=q.j->>''role_id''),''{}''::jsonb) j FROM ('||expected_query||') q';
     END IF;
""" + anchor)
    anchor = 'DO $reparent$'
    sql = sql.replace(anchor, "UPDATE role_skill_lineage r SET review_status=m.review_status FROM fix_mapping m WHERE r.role_id=m.role_id;\n" + anchor)
    # Save the exact user-approved metadata payloads from the release; add no
    # manual-review claims and retain the Low-confidence pending state.
    metadata = read(DATA / '01_TABLES/dataset_metadata.csv')
    assert len(metadata) == 655
    assert sum(json.loads(r['metadata_value'])['use_in_role_skills'] for r in metadata) == 442
    core = read(DATA / '01_TABLES/role_skills.csv')
    payload = ''.join('|'.join(r[k] for k in ('role_id','skill_id','skill_name','skill_type','importance')) + ';'
                      for r in sorted(core, key=lambda r: (r['role_id'], r['skill_id'])))
    core_md5 = hashlib.md5(payload.encode()).hexdigest()
    start = sql.index('INSERT INTO dataset_metadata(metadata_key,metadata_value)\nSELECT')
    end = sql.index('\\if :fix_commit', start)
    sql = sql[:start] + 'INSERT INTO dataset_metadata(metadata_key,metadata_value) VALUES\n' + ',\n'.join(
        '(' + literal(r['metadata_key']) + ',' + literal(r['metadata_value']) + '::jsonb)' for r in metadata
    ) + ';\n' + sql[end:]
    # Duplicates checked using both the backend key and a whitespace-normalized
    # key. No UNIQUE(ESCO) rule: shared comparison codes do not duplicate roles.
    guard = """
 IF EXISTS(SELECT 1 FROM roles GROUP BY lower(regexp_replace(btrim(role_title),'[[:space:]]+',' ','g')) HAVING count(*)>1)
 OR EXISTS(SELECT 1 FROM skill_taxonomy GROUP BY lower(regexp_replace(btrim(canonical_name),'[[:space:]]+',' ','g')) HAVING count(*)>1)
 OR EXISTS(SELECT 1 FROM role_skills GROUP BY role_id,skill_id HAVING count(*)>1)
 THEN RAISE EXCEPTION 'Invalid normalized duplicate remains'; END IF;
 IF (SELECT count(*) FROM skill_aliases)<>37284 OR (SELECT count(*) FROM skill_taxonomy)<>6121
 THEN RAISE EXCEPTION 'Unexpected alias or canonical concept count'; END IF;
 IF EXISTS(SELECT 1 FROM role_skill_lineage l JOIN fix_mapping m USING(role_id) WHERE l.review_status<>m.review_status)
 THEN RAISE EXCEPTION 'Lineage review status not synchronized'; END IF;
"""
    sql = sql.replace(" IF (SELECT count(*) FROM roles)<>662", guard + " IF (SELECT count(*) FROM roles)<>662")
    core_guard = """
 IF (SELECT md5(string_agg(role_id||'|'||skill_id||'|'||skill_name||'|'||skill_type||'|'||importance::integer::text||';','' ORDER BY role_id COLLATE "C",skill_id COLLATE "C"))
     FROM role_skills WHERE role_id ~ '^M[0-9]{6}$') <> 'CORE_MD5'
 THEN RAISE EXCEPTION 'Approved D13 skill rows do not match the cleaned CSV'; END IF;
""".replace('CORE_MD5', core_md5)
    sql = sql.replace('END $verify$;', core_guard + 'END $verify$;')
    sql = sql.replace(" 'historical_reference_rows_preserved',true));", " 'historical_reference_rows_preserved',true,\n 'backend_changed',false,'data_only_limitations_acknowledged',true,\n 'd13_core_csv_md5'," + literal(core_md5) + ",\n 'expected_table_fingerprints',(SELECT jsonb_agg(to_jsonb(x) ORDER BY table_name) FROM fix_expected x)));")
    # Report only aggregate non-personal results before the transaction ends.
    report = """
SELECT 'FINAL_COUNTS' marker,
 (SELECT count(*) FROM roles) roles,(SELECT count(*) FROM role_skills) role_skills,
 (SELECT count(*) FROM skill_aliases) aliases,(SELECT count(*) FROM skill_taxonomy) skills;
SELECT 'APPROVAL_COUNTS' marker, metadata_value->>'mapping_confidence' confidence,
 metadata_value->>'use_in_role_skills' approved,count(*) roles
FROM dataset_metadata WHERE starts_with(metadata_key,'d13_quality_fix_20260830.mapping.') GROUP BY 2,3 ORDER BY 2;
SELECT 'SCHEMA_UNCHANGED' marker,current_setting('quality_fix.schema_before') signature;
"""
    pos = sql.rindex('\\if :fix_commit')
    sql = sql[:pos] + report + sql[pos:]
    assert 'backend_compatibility_confirmed' not in sql
    assert not re.search(r'^\s*(ALTER|TRUNCATE|DROP)\s', sql, re.M | re.I)
    assert not re.search(r'^\s*CREATE\s+(?!TEMP\s)', sql, re.M | re.I)
    assert 'CASCADE' not in sql and '@@' not in sql
    assert sql.count('DELETE FROM') == 4
    assert sql.count('COMMIT;') == 1 and sql.count('ROLLBACK;') == 1
    output = ROOT / 'DATA_QUALITY_UPDATE.sql'
    output.write_text(sql)
    with (ROOT / 'DATA_QUALITY_UPDATE.sql.gz').open('wb') as stream:
        with gzip.GzipFile(filename='', fileobj=stream, mode='wb', mtime=0) as compressed:
            compressed.write(sql.encode())
    digest = hashlib.sha256(sql.encode()).hexdigest()
    manifest = {'status':'PREPARED_NOT_APPLIED', 'database':'rerouteher_test',
        'source_dataset':'ReRouteHer_Data_Quality_Fix_2026-08-30', 'sql_sha256':digest,
        'sql_bytes':len(sql.encode()), 'gzip_bytes':(ROOT / 'DATA_QUALITY_UPDATE.sql.gz').stat().st_size,
        'source_csv_counts':{'roles':655,'approved_mappings':442,'low_confidence_mappings':213,
                             'approved_role_skills':13147},
        'expected_database_counts':{'roles':662,'skill_taxonomy':6121,'role_skills':13266,
                                    'role_skill_lineage':13266,'skill_aliases':37284},
        'legacy_roles_retired':{'R01':'M251201','R02':'M252403','R06':'M254302'},
        'deleted_role_skill_rows':27911,'deleted_lineage_rows':27928,
        'deleted_ambiguous_alias_rows':446,'permanent_schema_changed':False,
        'backend_changes':False,'requires_action_time_deletion_confirmation':True,
        'sql_execution_tested':False}
    (ROOT / 'preparation.json').write_text(json.dumps(manifest, indent=2) + '\n')
    schema_start = sql.index(' SELECT md5(jsonb_build_object(')
    schema_end = sql.index(' INTO fp;', schema_start)
    schema_query = sql[schema_start:schema_end]
    postcheck = """-- Read-only verification of the committed data quality update.
\\set ON_ERROR_STOP on
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
 SCHEMA_QUERY INTO schema_fp;
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
SELECT 'source_core_hash' marker,md5(string_agg(role_id||'|'||skill_id||'|'||skill_name||'|'||skill_type||'|'||importance::integer::text||';','' ORDER BY role_id COLLATE "C",skill_id COLLATE "C"))='CORE_MD5' matches_csv
FROM role_skills WHERE role_id ~ '^M[0-9]{6}$';
SELECT 'cases' marker,r.role_id,r.role_title,r.esco_code,count(s.skill_id) core_skills FROM roles r LEFT JOIN role_skills s USING(role_id)
WHERE r.role_id IN ('M232102','M151108','M251201','M252403','M254302') GROUP BY r.role_id ORDER BY r.role_id;
SELECT 'valid_shared_esco_groups' marker,count(*) FROM (SELECT esco_code FROM roles GROUP BY esco_code HAVING count(*)>1) q;
COMMIT;
\\echo DATA_QUALITY_POSTCHECKS_PASSED
""".replace('SCHEMA_QUERY', schema_query).replace('CORE_MD5', core_md5)
    (ROOT / 'VERIFY_DATA_QUALITY_UPDATE.sql').write_text(postcheck)
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
