"""Data-only import into an EMPTY copy of the existing schema, never a migration.

The current rerouteher_test contains reused six-digit identifiers. Refuse it.
No schema creation, row removal, overwrites or remote execution are performed.
"""
from pathlib import Path
import csv, json, re, hashlib, collections

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT.parent/'ReRouteHer_D13_FINAL_2026-08-30'
PREFIX='d13_masco2020_test_20260830'
TARGET_DATABASE='rerouteher_masco2020_test'
MODEL='sentence-transformers/all-MiniLM-L6-v2'

def read(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def lit(v):
    if v is None:return 'NULL'
    if isinstance(v,bool):return 'TRUE' if v else 'FALSE'
    if isinstance(v,(int,float)):return str(v)
    return "E'"+str(v).replace('\\','\\\\').replace("'","''").replace('\r','\\r').replace('\n','\\n').replace('\t','\\t')+"'"
def js(v):return lit(json.dumps(v,ensure_ascii=False,separators=(',',':')))+'::jsonb'

def build():
    schema=(ROOT/'00_SOURCE_SNAPSHOT/user_existing_schema.sql').read_text()
    structs={}
    for name,body in re.findall(r'CREATE TABLE IF NOT EXISTS rerouteher\.(\w+)\s*\((.*?)\n\);',schema,re.S):
        cols={}
        for line in body.splitlines():
            line=line.strip()
            if not line or line.startswith('CONSTRAINT'):continue
            m=re.match(r'(\w+)\s+(.+?)(?:,)?$',line)
            if m:cols[m[1]]=m[2]
        structs[name]=cols
    roles=read(ROOT/'01_TABLES/D11_STEM_roles.csv')
    tx=read(ROOT/'01_TABLES/skill_taxonomy.csv');aliases=read(ROOT/'01_TABLES/skill_aliases.csv')
    links=read(ROOT/'01_TABLES/role_skills_lineage.csv')
    cov=read(ROOT/'01_TABLES/D13_role_esco_coverage.csv')
    skill_lineage={r['skill_id']:r for r in read(ROOT/'01_TABLES/skill_taxonomy_lineage.csv')}
    raw={r['conceptUri']:r for r in sorted(read(OLD/'00_SOURCE_SNAPSHOT/ESCO_v1.2.1_classification_en_csv/skills_en.csv'),key=lambda r:r['modifiedDate'])}
    digital_scheme='http://data.europa.eu/esco/concept-scheme/6c930acd-c104-4ece-acf7-f44fd7333036'
    skill_types={};metadata=[]
    for r in tx:
        s=raw[skill_lineage[r['skill_id']]['concept_uri']]
        schemes=s['inScheme'].replace('\n','').split(',')
        if digital_scheme in schemes or any(x.endswith('/digcomp') for x in schemes):
            category,rule='digital','ESCO digital/DigComp collection membership'
        elif s['skillType']!='knowledge' and s['reuseLevel']=='transversal':
            category,rule='soft','Non-knowledge transversal ESCO skill; coarse test bucket'
        else:category,rule='technical','Default test compatibility bucket; not an official ESCO type'
        skill_types[r['skill_id']]=category
        metadata.append((PREFIX+'.skill_type.'+r['skill_id'],{'skill_id':r['skill_id'],'concept_uri':s['conceptUri'],
            'original_esco_skill_type':s['skillType'],'dataset_skill_type':r['skill_type'],
            'database_skill_type':category,'adapter_rule':rule,'esco_reuse_level':s['reuseLevel'],
            'esco_in_scheme':s['inScheme'],'official_category_crosswalk':False}))
    rolecols=list(structs['roles']);role_rows=[]
    numeric={'remote_task_count','remote_capable_tasks','remote_onsite_tasks','remote_unclear_tasks','ai_exposure_share','ai_exposure_external_score_0_100'}
    for r in roles:
        row=[]
        for k in rolecols:
            if k=='role_embedding':v=r['role_embedding_384']
            elif k=='flexible_role':v=r[k].lower()=='true'
            elif k in numeric:v=(int(r[k]) if 'integer' in structs['roles'][k] else float(r[k])) if r[k] else None
            else:v=r.get(k,'')
            row.append(v)
        role_rows.append(row)
    data={
        'roles':(rolecols,role_rows),
        'skill_taxonomy':(['skill_id','canonical_name','definition','skill_type','competence_area','level','source_framework','source_id','embedding_model','embedding'],
            [[r['skill_id'],r['canonical_name'],r['definition'],skill_types[r['skill_id']],None,None,'ESCO v1.2.1',skill_lineage[r['skill_id']]['concept_uri'],MODEL,r['embedding']] for r in tx]),
        'skill_aliases':(['skill_id','alias','alias_source'],[[r[k] for k in ['skill_id','alias','alias_source']] for r in aliases]),
        'role_skills':(['role_id','skill_id','skill_name','skill_type','importance','source','source_occupation_code','source_element_id','importance_method','curation_note'],[]),
        'role_skill_lineage':(['role_id','skill_id','skill_name','skill_type','importance','source','source_occupation_code','source_element_id','importance_method','curation_note','raw_source_value','normalisation_or_rating_rule','one_line_justification','source_url','review_status'],[]),
    }
    for r in links:
        note=f"TEST ONLY; MASCO 2020 identity with inherited ESCO proxy. See dataset_metadata {PREFIX}.mapping.{r['role_id']} and {PREFIX}.skill_type.{r['skill_id']}"
        base=[r['role_id'],r['skill_id'],r['skill_name'],skill_types[r['skill_id']],int(r['importance']),
            'ESCO v1.2.1 / MASCO 2020 project test mapping',r['esco_code'],r['skill_uri'],'ESCO essential=100; optional=50',note]
        data['role_skills'][1].append(base)
        data['role_skill_lineage'][1].append(base+[r['relation_type'],'100 if essential; 50 if optional; no local re-rating',
            f"Inherited test proxy: {r['mapping_relation']}; confidence={r['mapping_confidence']}",r['esco_occupation_uri'],'test_only_project_mapping'])
    for tab,(cols,rows) in data.items():
        assert not set(cols)-set(structs[tab]),tab
        required={k for k,v in structs[tab].items() if 'NOT NULL' in v}
        assert required<=set(cols),(tab,required-set(cols))
        for row in rows:
            assert len(row)==len(cols)
            assert all(v is not None for k,v in zip(cols,row) if k in required),tab
    metadata += [(PREFIX+'.mapping.'+r['role_id'],r) for r in cov]
    metadata += [(PREFIX+'.source_esco.'+r['source_current_role_id'],r) for r in read(ROOT/'01_TABLES/ESCO_comparison_preservation.csv')]
    # One-to-many remaps require a composite metadata key, including exclusions.
    metadata += [(PREFIX+'.crosswalk.'+r['source_current_role_id']+'.'+(r['masco2020_code'] or 'excluded'),r) for r in read(ROOT/'01_TABLES/MASCO2020_role_crosswalk.csv')]
    summary=json.loads((ROOT/'02_QA/build_summary.json').read_text())
    metadata += [(PREFIX+'.release',dict(summary,sql_target_database=TARGET_DATABASE,
        prior_release_migration=False,import_requires_empty_data_tables=True,
        skill_type_adapter_counts=dict(collections.Counter(skill_types.values()))))]
    out=ROOT/'04_DATABASE/MASCO2020_LOAD_EMPTY_TEST_SCHEMA.sql'
    with out.open('w',encoding='utf-8') as f:
        f.write('''-- MASCO 2020 STEM TEST SNAPSHOT. This is NOT an append/migration for rerouteher_test.
-- Requires an empty copy of the existing rerouteher schema in rerouteher_masco2020_test.
-- This file creates no tables and removes or overwrites no rows.
-- Self-contained data. Execute the WHOLE file with psql -v ON_ERROR_STOP=1 -f FILE.
BEGIN;
SET LOCAL lock_timeout='15s';
SET LOCAL statement_timeout='0';
SET LOCAL standard_conforming_strings=on;
''')
        f.write(f"DO $m20$ BEGIN IF current_database()<>{lit(TARGET_DATABASE)} THEN RAISE EXCEPTION 'Wrong database: use a separate empty rerouteher_masco2020_test, never the existing rerouteher_test'; END IF; END $m20$;\n")
        f.write("SELECT pg_advisory_xact_lock(hashtext('rerouteher_masco2020_test_20260830'));\n")
        f.write('LOCK TABLE '+', '.join('rerouteher.'+t for t in list(data)+['dataset_metadata'])+' IN SHARE ROW EXCLUSIVE MODE;\n')
        f.write('DO $m20$ BEGIN\n')
        for tab in data:
            f.write(f"IF EXISTS(SELECT 1 FROM rerouteher.{tab}) THEN RAISE EXCEPTION 'Target table {tab} is not empty. No migration or replacement is performed.'; END IF;\n")
        f.write(f"IF EXISTS(SELECT 1 FROM rerouteher.dataset_metadata WHERE metadata_key LIKE '{PREFIX}.%') THEN RAISE EXCEPTION 'MASCO 2020 import metadata already exists. Import refused.'; END IF;\nEND $m20$;\n")
        for tab,(cols,rows) in data.items():
            f.write(f'\n-- {tab}: {len(rows)} rows\n')
            for start in range(0,len(rows),250):
                f.write(f'INSERT INTO rerouteher.{tab} ({", ".join(cols)}) VALUES\n')
                f.write(',\n'.join('('+','.join(lit(v) for v in row)+')' for row in rows[start:start+250])+';\n')
        for start in range(0,len(metadata),100):
            f.write('INSERT INTO rerouteher.dataset_metadata(metadata_key,metadata_value) VALUES\n')
            f.write(',\n'.join('('+lit(k)+','+js(v)+')' for k,v in metadata[start:start+100])+';\n')
        f.write('DO $m20$ DECLARE n integer; BEGIN\n')
        for tab,(_,rows) in data.items():
            f.write(f"SELECT count(*) INTO n FROM rerouteher.{tab}; IF n<>{len(rows)} THEN RAISE EXCEPTION 'Unexpected {tab} count: %',n; END IF;\n")
        f.write(f"SELECT count(*) INTO n FROM rerouteher.dataset_metadata WHERE metadata_key LIKE '{PREFIX}.%'; IF n<>{len(metadata)} THEN RAISE EXCEPTION 'Unexpected metadata count: %',n; END IF;\n")
        f.write('END $m20$;\nCOMMIT;\n')
        f.write("SELECT count(*) AS masco2020_roles FROM rerouteher.roles;\n")
    text=out.read_text()
    assert not re.search(r'^\s*(CREATE|ALTER|DROP|TRUNCATE|DELETE|UPDATE)\s',text,re.M|re.I)
    assert 'ON CONFLICT' not in text and '\\copy' not in text
    assert text.count('BEGIN;')==1 and text.count('COMMIT;')==1
    assert set(re.findall(r'INSERT INTO rerouteher\.(\w+)',text))==set(data)|{'dataset_metadata'}
    report={'structural_validation':'PASS','target_database':TARGET_DATABASE,'requires_empty_data_tables':list(data),
        'schema_changed':False,'overwrites_or_deletions':False,'live_database_executed':False,
        'insert_rows':{t:len(rows) for t,(_,rows) in data.items()},'metadata_rows':len(metadata),
        'skill_type_adapter_counts':dict(collections.Counter(skill_types.values())),
        'sql_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'sql_bytes':out.stat().st_size,
        'validation_scope':'Generated columns, required values, transaction/guard structure and row counts; not executed against a database.'}
    (ROOT/'02_QA/sql_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':build()
