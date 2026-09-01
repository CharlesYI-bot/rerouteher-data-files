"""Self-contained data-only PostgreSQL import for the user's exact existing schema.

No CREATE/ALTER/DROP/TRUNCATE/DELETE statements. New rows are appended.
Existing matching D11 roles may have only esco_code updated; the prior row is
snapshotted in the existing dataset_metadata table before that update.
"""
from pathlib import Path
import argparse, collections, csv, gzip, hashlib, json, re, shutil
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
SCHEMA_INPUT=Path('/Users/charlesyi/.codex/attachments/02839472-34d1-4244-a2f2-5b8f2ed2041c/pasted-text.txt')
PREFIX='d13_test_20260830'
MODEL='sentence-transformers/all-MiniLM-L6-v2'
SOURCE='ESCO v1.2.1 D13 test mapping 2026-08-30'
def read(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def lit(v):
    if v is None:return 'NULL'
    if isinstance(v,bool):return 'TRUE' if v else 'FALSE'
    if isinstance(v,(int,float)):return str(v)
    return "E'"+str(v).replace('\\','\\\\').replace("'","''").replace('\r','\\r').replace('\n','\\n').replace('\t','\\t')+"'"
def jlit(v):return lit(json.dumps(v,ensure_ascii=False,separators=(',',':')))+'::jsonb'

def build(live_compat=False):
    db=ROOT/'04_DATABASE';db.mkdir(exist_ok=True)
    snapshot=ROOT/'00_SOURCE_SNAPSHOT/user_existing_schema.sql'
    if SCHEMA_INPUT.exists():shutil.copy2(SCHEMA_INPUT,snapshot)
    schema=snapshot.read_text()
    structs={}
    for table,body in re.findall(r'CREATE TABLE IF NOT EXISTS rerouteher\.(\w+)\s*\((.*?)\n\);',schema,re.S):
        cols={}
        for line in body.splitlines():
            line=line.strip()
            if not line or line.startswith('CONSTRAINT'):continue
            m=re.match(r'(\w+)\s+(.+?)(?:,)?$',line)
            if m:cols[m[1]]=m[2]
        structs[table]=cols
    tx=read(ROOT/'01_TABLES/skill_taxonomy.csv');al=read(ROOT/'01_TABLES/skill_aliases.csv')
    rs=read(ROOT/'01_TABLES/role_skills.csv');ln=read(ROOT/'01_TABLES/role_skills_lineage.csv')
    cov=read(ROOT/'01_TABLES/D13_role_esco_coverage.csv');cb={r['role_id']:r for r in cov}
    roles=read(ROOT/'00_SOURCE_SNAPSHOT/D11_STEM_roles.csv')
    # Live pg18 checks were absent from the user's ERD export. Keep the source
    # tables unchanged and adapt only the import's legacy three-way category.
    skill_types={r['skill_id']:r['skill_type'] for r in tx}
    type_metadata=[]
    if live_compat:
        source_rows=read(ROOT/'00_SOURCE_SNAPSHOT/ESCO_v1.2.1_classification_en_csv/skills_en.csv')
        raw={r['conceptUri']:r for r in sorted(source_rows,key=lambda r:r['modifiedDate'])}
        lineage={r['skill_id']:r for r in read(ROOT/'01_TABLES/skill_taxonomy_lineage.csv')}
        digital_scheme='http://data.europa.eu/esco/concept-scheme/6c930acd-c104-4ece-acf7-f44fd7333036'
        for r in tx:
            s=raw[lineage[r['skill_id']]['concept_uri']]
            schemes=s['inScheme'].replace('\n','').split(',')
            if digital_scheme in schemes or any(x.endswith('/digcomp') for x in schemes):
                category,rule='digital','ESCO digital/DigComp collection membership'
            elif s['skillType']!='knowledge' and s['reuseLevel']=='transversal':
                category,rule='soft','Non-knowledge ESCO transversal skill; coarse test compatibility bucket'
            else:
                category,rule='technical','Default test compatibility bucket, not an official ESCO type'
            skill_types[r['skill_id']]=category
            type_metadata.append((PREFIX+'.skill_type.'+r['skill_id'],{
                'skill_id':r['skill_id'],'concept_uri':s['conceptUri'],
                'original_esco_skill_type':s['skillType'],'dataset_skill_type':r['skill_type'],
                'esco_reuse_level':s['reuseLevel'],'esco_in_scheme':s['inScheme'],
                'database_skill_type':category,'adapter_rule':rule,
                'purpose':'test_only_schema_compatibility','official_category_crosswalk':False}))
    rolecols=list(structs['roles'])
    numbercols={'remote_task_count','remote_capable_tasks','remote_onsite_tasks','remote_unclear_tasks','ai_exposure_share','ai_exposure_external_score_0_100'}
    rows=[]
    for r in roles:
        out=[]
        for k in rolecols:
            if k=='esco_code':v=cb[r['role_id']]['chosen_esco_code']
            elif k=='role_embedding':
                a=np.array(json.loads(r['role_embedding_384']),dtype=float)
                assert a.shape==(384,) and np.isfinite(a).all() and abs(np.linalg.norm(a)-1)<1e-4
                v=r['role_embedding_384']
            elif k=='flexible_role':v=r[k].lower()=='true'
            elif k in numbercols:v=(int(r[k]) if 'integer' in structs['roles'][k] else float(r[k])) if r[k] else None
            else:v=r.get(k,'')
            out.append(v)
        rows.append(out)
    data={
      'roles':(rolecols,rows),
      'skill_taxonomy':(['skill_id','canonical_name','definition','skill_type','competence_area','level','source_framework','source_id','embedding_model','embedding'],
        [[r['skill_id'],r['canonical_name'],r['definition'],skill_types[r['skill_id']],None,None,'ESCO v1.2.1','http://data.europa.eu/esco/skill/'+r['skill_id'],MODEL,r['embedding']] for r in tx]),
      'skill_aliases':(['skill_id','alias','alias_source'],[[r[k] for k in ['skill_id','alias','alias_source']] for r in al]),
      'role_skills':(['role_id','skill_id','skill_name','skill_type','importance','source','source_occupation_code','source_element_id','importance_method','curation_note'],[]),
      'role_skill_lineage':(['role_id','skill_id','skill_name','skill_type','importance','source','source_occupation_code','source_element_id','importance_method','curation_note','raw_source_value','normalisation_or_rating_rule','one_line_justification','source_url','review_status'],[])
    }
    # Use actual source URIs (including any non-standard ESCO concept scheme).
    skilluri={r['skill_id']:r['concept_uri'] for r in read(ROOT/'01_TABLES/skill_taxonomy_lineage.csv')}
    for row in data['skill_taxonomy'][1]:row[7]=skilluri[row[0]]
    for r in ln:
        c=cb[r['role_id']]
        note=f"TEST ONLY; {c['mapping_relation']}; confidence={c['mapping_confidence']}; {c['mapping_rationale']}"
        if live_compat:note+=f"; original_ESCo_skill_type={r['skill_type']}; database type is a test compatibility bucket; see {PREFIX}.skill_type.{r['skill_id']}"
        base=[r['role_id'],r['skill_id'],r['skill_name'],skill_types[r['skill_id']],int(r['importance']),SOURCE,r['esco_code'],r['skill_uri'],'ESCO essential=100; optional=50',note]
        data['role_skills'][1].append(base)
        data['role_skill_lineage'][1].append(base+[r['relation_type'],'100 if essential; 50 if optional; no local re-rating',c['mapping_rationale'],r['esco_occupation_uri'],'test_only_project_mapping'])
    # Validate every inserted column against the supplied schema, including NOT NULL.
    for tab,(cols,rws) in data.items():
        assert not set(cols)-set(structs[tab]),(tab,set(cols)-set(structs[tab]))
        required={k for k,v in structs[tab].items() if 'NOT NULL' in v}
        assert required<=set(cols),(tab,required-set(cols))
        for row in rws:
            assert len(row)==len(cols)
            assert all(v is not None for k,v in zip(cols,row) if k in required),tab
    assert {'metadata_key','metadata_value'}<=set(structs['dataset_metadata'])
    out=db/('D13_APPEND_LIVE_COMPAT.sql' if live_compat else 'D13_APPEND_EXISTING_SCHEMA.sql')
    with out.open('w',encoding='utf-8') as f:
        f.write('''-- D13 TEST DATA — existing rerouteher schema, embedded data, no schema changes.
-- Open this entire file in pgAdmin Query Tool and execute, or use psql -v ON_ERROR_STOP=1 -f FILE.
-- Appends missing rows. Existing matching D11 roles: ONLY esco_code is updated.
-- Existing skill/alias/link rows are kept on key conflicts; no old links are removed.
-- Prior affected roles are preserved in dataset_metadata under d13_test_20260830.before_role.*.
-- One transaction: any failure rolls back all changes. No external CSV files are required.
BEGIN;
SET LOCAL lock_timeout = '15s';
SET LOCAL statement_timeout = '0';
SET LOCAL standard_conforming_strings = on;
''')
        if live_compat:
            f.write("-- Live compatibility variant: raw ESCO categories retained in dataset_metadata.\n")
            f.write("DO $d13$ BEGIN IF current_database()<>'rerouteher_test' THEN RAISE EXCEPTION 'This import is restricted to rerouteher_test'; END IF; END $d13$;\n")
        # Serialize concurrent imports and protect the before-image and compatibility check.
        f.write("SELECT pg_advisory_xact_lock(hashtext('rerouteher_d13_test_20260830'));\n")
        f.write('LOCK TABLE rerouteher.roles, rerouteher.skill_taxonomy IN SHARE ROW EXCLUSIVE MODE;\n')
        # Role ID collisions must never replace a different occupation's ESCO code.
        ids=',\n'.join('('+lit(r['role_id'])+','+lit(r['masco_code'])+')' for r in roles)
        f.write("DO $d13$ BEGIN\nIF EXISTS (SELECT 1 FROM (VALUES\n"+ids+") AS incoming(role_id,masco_code) JOIN rerouteher.roles existing USING(role_id) WHERE existing.masco_code IS DISTINCT FROM incoming.masco_code) THEN RAISE EXCEPTION 'D13 role-ID collision: existing MASCO code differs. No changes applied.'; END IF;\nEND $d13$;\n")
        ids_sql=','.join(lit(r['role_id']) for r in roles)
        f.write(f"INSERT INTO rerouteher.dataset_metadata(metadata_key,metadata_value) SELECT {lit(PREFIX+'.before_role.')} || r.role_id, to_jsonb(r) FROM rerouteher.roles r WHERE r.role_id IN ({ids_sql}) ON CONFLICT(metadata_key) DO NOTHING;\n")
        # Refuse incompatible skill identities rather than silently linking old definitions.
        identities=',\n'.join('('+lit(r['skill_id'])+','+lit(r['canonical_name'])+','+lit(skill_types[r['skill_id']])+')' for r in tx)
        f.write("DO $d13$ BEGIN\nIF EXISTS (SELECT 1 FROM (VALUES\n"+identities+") AS incoming(skill_id,canonical_name,skill_type) JOIN rerouteher.skill_taxonomy existing USING(skill_id) WHERE existing.canonical_name IS DISTINCT FROM incoming.canonical_name OR existing.skill_type IS DISTINCT FROM incoming.skill_type) THEN RAISE EXCEPTION 'D13 skill-ID collision: existing name/type differs. No changes applied.'; END IF;\nEND $d13$;\n")
        for tab,(cols,rws) in data.items():
            f.write(f'\n-- {tab}: {len(rws)} input rows\n')
            for start in range(0,len(rws),250):
                f.write(f'INSERT INTO rerouteher.{tab} ({", ".join(cols)}) VALUES\n')
                f.write(',\n'.join('('+','.join(lit(v) for v in row)+')' for row in rws[start:start+250]))
                if tab=='roles':
                    f.write('\nON CONFLICT(role_id) DO UPDATE SET esco_code=EXCLUDED.esco_code WHERE rerouteher.roles.masco_code=EXCLUDED.masco_code AND rerouteher.roles.esco_code IS DISTINCT FROM EXCLUDED.esco_code;\n')
                else:f.write('\nON CONFLICT DO NOTHING;\n')
        metadata=[(PREFIX+'.release',{'purpose':'test_only','roles':657,'newly_mapped_roles':562,'skills':len(tx),'aliases':len(al),'role_skill_links':len(rs),'schema_unchanged':True,'role_conflict_rule':'Only esco_code updated for identical six-digit MASCO role identity; before-image retained.','skill_conflict_rule':'Existing skills, aliases and links preserved. Conflicting skill identity aborts.','old_links_removed':False,'mapping_is_official_crosswalk':False})]
        metadata += [(PREFIX+'.mapping.'+c['role_id'],c) for c in cov]
        if live_compat:
            metadata[0][1]['skill_type_adapter']={'purpose':'test_only_schema_compatibility','original_esco_types_retained_in_metadata':True,'source_tables_changed':False,'category_counts':dict(collections.Counter(skill_types.values()))}
            metadata+=type_metadata
        for start in range(0,len(metadata),100):
            f.write('INSERT INTO rerouteher.dataset_metadata(metadata_key,metadata_value) VALUES\n')
            f.write(',\n'.join('('+lit(k)+','+jlit(v)+')' for k,v in metadata[start:start+100]))
            f.write('\nON CONFLICT(metadata_key) DO NOTHING;\n')
        # Whole-scope expected row presence is checked before commit (not table totals).
        f.write("DO $d13$ DECLARE n integer; BEGIN\n")
        f.write(f"SELECT count(*) INTO n FROM rerouteher.roles WHERE role_id IN ({ids_sql}); IF n<>657 THEN RAISE EXCEPTION 'Expected 657 D11 roles, got %',n; END IF;\n")
        f.write(f"SELECT count(*) INTO n FROM rerouteher.dataset_metadata WHERE metadata_key LIKE '{PREFIX}.mapping.%'; IF n<>657 THEN RAISE EXCEPTION 'Expected 657 D13 mapping records, got %',n; END IF;\nEND $d13$;\nCOMMIT;\n")
        f.write(f"SELECT 'D13 mappings' AS metric, count(*) AS rows FROM rerouteher.dataset_metadata WHERE metadata_key LIKE '{PREFIX}.mapping.%';\n")
        f.write(f"SELECT r.role_id,r.role_title,r.masco_code,r.esco_code,m.metadata_value->>'mapping_relation' AS mapping_relation,m.metadata_value->>'mapping_confidence' AS mapping_confidence FROM rerouteher.roles r JOIN rerouteher.dataset_metadata m ON m.metadata_key='{PREFIX}.mapping.'||r.role_id ORDER BY r.role_id;\n")
    # Streaming lexical validation: DDL is absent from executable statement starts.
    text=out.read_text()
    assert not re.search(r'^\s*(CREATE|ALTER|DROP|TRUNCATE|DELETE)\s',text,re.M|re.I)
    assert '\\copy' not in text and '\\i ' not in text and 'COPY ' not in text
    assert text.count('BEGIN;')==1 and text.count('COMMIT;')==1
    assert set(re.findall(r'INSERT INTO rerouteher\.(\w+)',text))==set(data)|{'dataset_metadata'}
    with out.open('rb') as inp,gzip.open(str(out)+'.gz','wb',compresslevel=6) as zipped:shutil.copyfileobj(inp,zipped)
    digest=hashlib.sha256(out.read_bytes()).hexdigest()
    (db/(out.name+'.sha256')).write_text(digest+'  '+out.name+'\n')
    report={'validation_passed':True,'schema_source_sha256':hashlib.sha256(snapshot.read_bytes()).hexdigest(),'schema_source_tables':len(structs),'insert_input_rows':{t:len(rows) for t,(cols,rows) in data.items()},'mapping_metadata_rows':657,'release_metadata_rows':1,'before_image_rows':'0 to 657 depending on existing roles','allowed_existing_update':'roles.esco_code only; same role_id and masco_code','DDL_statements':0,'delete_truncate_statements':0,'schema_changes':False,'external_file_dependencies':False,'live_database_executed':False,'sql_sha256':digest,'sql_bytes':out.stat().st_size}
    if live_compat:
        assert set(skill_types.values())<={'technical','soft','digital'}
        assert len(type_metadata)==len(tx)==6164
        report['skill_type_adapter']={'metadata_rows':len(type_metadata),'category_counts':dict(collections.Counter(skill_types.values())),'source_tables_unchanged':True,'target_database_guard':'rerouteher_test'}
    report_name='D13_live_compat_sql_validation.json' if live_compat else 'D13_append_sql_validation.json'
    (ROOT/'02_QA'/report_name).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--live-compat',action='store_true',help='Adapt skill categories for the verified rerouteher_test CHECK constraints.')
    build(live_compat=parser.parse_args().live_compat)
