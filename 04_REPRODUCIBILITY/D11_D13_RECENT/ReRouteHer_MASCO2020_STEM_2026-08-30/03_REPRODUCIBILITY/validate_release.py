"""Read-only consistency checks for the authored MASCO 2020 release."""
from pathlib import Path
import csv,json,re,hashlib,collections,zipfile,xml.etree.ElementTree as ET
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT.parent/'ReRouteHer_D13_FINAL_2026-08-30'
D11=ROOT.parent/'ReRouteHer_D11_STEM_2026-08-29'
checks=[]
def read(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(name,condition,detail=''):
    assert condition,(name,detail)
    checks.append({'check':name,'result':'PASS','detail':detail})
def unique(rows,*keys):return len(rows)==len({tuple(r[k] for k in keys) for r in rows})

def validate():
    roles=read(ROOT/'01_TABLES/D11_STEM_roles.csv');by_role={r['role_id']:r for r in roles}
    current=read(ROOT/'00_SOURCE_SNAPSHOT/D11_current_STEM_roles.csv');cur={r['role_id']:r for r in current}
    rb={r['masco_6d_code'].replace('-',''):r for r in read(ROOT/'00_SOURCE_SNAPSHOT/MASCO_2020_individual_occupations_en.csv')}
    crosswalk=read(ROOT/'01_TABLES/MASCO2020_role_crosswalk.csv')
    excluded=read(ROOT/'01_TABLES/MASCO2020_excluded_roles.csv')
    primary=json.loads((ROOT/'02_QA/selected_profiles.json').read_text())['primary_source_by_target']
    check('655 unique six-digit 2020 role identities',len(roles)==655 and unique(roles,'role_id') and unique(roles,'masco_code') and all(re.fullmatch(r'\d{6}',r['masco_code']) and r['role_id']=='M'+r['masco_code'] for r in roles))
    check('Every output code/title equals the 2020 registry',all(r['role_title']==rb[r['masco_code']]['masco_occupation_title_en']==r['masco_title'] for r in roles))
    check('D1-compatible first 24 role fields preserved',list(roles[0])[:24]==list(current[0])[:24])
    kept={r['source_current_role_id'] for r in crosswalk if r['status']=='retained'}
    removed={r['source_current_role_id'] for r in excluded}
    check('657 original sources accounted for: 638 retained, 19 excluded',len(kept)==638 and len(removed)==19 and kept|removed==set(cur) and not kept&removed)
    check('675 audit rows: splits and duplicate reconciled',len(crosswalk)==675 and len([r for r in crosswalk if r['status']=='retained'])==656 and len(primary)==655)
    check('No excluded source profile used by an output role',not set(primary.values())&removed)
    check('Exact source wins duplicate mechatronics target',primary['311524']=='M311506')
    check('STEM scope inherited, with explicit year/profile caveats',all(r['category_stem'].lower()=='true' and 'not a historical 2020' in r['stem_membership_basis'] and r['rating_status']=='inherited_pre_rating_not_2020_validated' for r in roles))
    check('Hierarchy prefixes consistent',all(r['masco_unit_group_code']==r['masco_code'][:4] and r['masco_minor_group_code']==r['masco_code'][:3] and r['masco_sub_major_group_code']==r['masco_code'][:2] and r['masco_major_group_code']==r['masco_code'][:1] for r in roles))
    pages=json.loads((ROOT/'02_QA/masco2020_pdf_pages.json').read_text())
    check('2020 code present on every cited PDF index page',all(r['masco_code_printed'] in re.sub(r'\s+','',pages[int(r['masco2020_source_pdf_page'])-1]) for r in roles))

    cov=read(ROOT/'01_TABLES/D13_role_esco_coverage.csv');cb={r['role_id']:r for r in cov}
    oldcov={r['role_id']:r for r in read(OLD/'01_TABLES/D13_role_esco_coverage.csv')}
    check('All 655 retained ESCO assignments equal primary source assignments',len(cov)==655 and set(cb)==set(by_role) and all(r['esco_code']==cb[r['role_id']]['chosen_esco_code']==oldcov[r['source_current_role_id']]['chosen_esco_code'] and r['esco_code'] for r in roles))
    comparisons=read(ROOT/'01_TABLES/ESCO_comparison_preservation.csv')
    compare_fields={'d13_esco_code':'chosen_esco_code','d13_esco_title':'chosen_esco_title','d11_esco_code':'d11_esco_code',
        'd11_esco_comparison_codes':'d11_esco_comparison_codes','d11_esco_comparison_titles':'d11_esco_comparison_titles',
        'previous_d13_esco_code':'previous_d13_esco_code','source_mapping_relation':'mapping_relation','source_mapping_confidence':'mapping_confidence'}
    check('Original ESCO comparison fields preserved for all 657 sources',len(comparisons)==657 and unique(comparisons,'source_current_role_id') and all(all(r[k]==oldcov[r['source_current_role_id']][v] for k,v in compare_fields.items()) for r in comparisons))
    check('Ambiguous remaps do not inherit an unsupported close-match claim',all(c['mapping_relation']=='inherited_test_proxy' for c in cov if c['masco2020_remap_method'] in ['combined_title_split','reviewed_functional_equivalent','duplicate_2020_title_canonical_choice']))
    check('No production-ready or human-reviewed claims introduced',all(c['production_ready'].lower()=='false' and c['review_status']=='test_only_project_mapping_not_human_validated' for c in cov))
    for r in roles:
        old=cur[r['source_current_role_id']]
        for field in ['task_summary','occupation_description','remote_possibility','remote_task_count','remote_capable_tasks','remote_onsite_tasks','remote_unclear_tasks','remote_justification','ai_exposure','ai_exposure_share','flexible_role']:
            assert r[field]==old[field],(r['role_id'],field)
    check('Task profiles and remote/AI pre-ratings retained without unsupported rerating',True)
    tasks=read(ROOT/'01_TABLES/D11_STEM_role_tasks.csv');ratings=read(ROOT/'01_TABLES/D11_STEM_task_rating_lineage.csv')
    taskcounts=collections.Counter(r['role_id'] for r in tasks)
    check('5512 tasks and rating references have valid unique keys',len(tasks)==len(ratings)==5512 and unique(tasks,'masco_task_id') and {r['masco_task_id'] for r in tasks}=={r['masco_task_id'] for r in ratings} and set(taskcounts)==set(by_role))
    check('Per-role task counts reconcile',all(taskcounts[r['role_id']]==int(r['remote_task_count']) for r in roles))
    old_tasks={r['masco_task_id']:r for r in read(D11/'01_TABLES/D11_STEM_role_tasks.csv')}
    check('Inherited task wording and source linkage preserved',all(r['task']==old_tasks[r['source_current_masco_task_id']]['task'] and r['source_current_role_id']==old_tasks[r['source_current_masco_task_id']]['role_id'] for r in tasks))
    for name in ['D11_STEM_role_rating_lineage.csv','D13_role_esco_mapping_review.csv','D13_mapping_evidence.csv']:
        rows=read(ROOT/'01_TABLES'/name)
        check(name+' has exactly one row per role',len(rows)==655 and {r['role_id'] for r in rows}==set(by_role))

    tx=read(ROOT/'01_TABLES/skill_taxonomy.csv');skills={r['skill_id'] for r in tx}
    links=read(ROOT/'01_TABLES/role_skills.csv');lineage=read(ROOT/'01_TABLES/role_skills_lineage.csv')
    aliases=read(ROOT/'01_TABLES/skill_aliases.csv')
    check('6051 skills are exactly the referenced skill set',len(tx)==len(skills)==6051 and skills=={r['skill_id'] for r in links})
    check('41286 links: unique keys and all role/skill foreign keys valid',len(links)==41286 and unique(links,'role_id','skill_id') and all(r['role_id'] in by_role and r['skill_id'] in skills for r in links))
    check('Role-skill lineage matches every link',len(lineage)==len(links) and {(r['role_id'],r['skill_id']) for r in lineage}=={(r['role_id'],r['skill_id']) for r in links})
    check('37521 aliases retain valid skill references and unique keys',len(aliases)==37521 and unique(aliases,'skill_id','alias') and all(r['skill_id'] in skills for r in aliases))
    oldlinks={(r['role_id'],r['skill_id']):r for r in read(OLD/'01_TABLES/role_skills.csv')}
    check('Every retained/split role-skill relationship equals its source relationship',all(all(r[k]==oldlinks[(r['source_current_role_id'],r['skill_id'])][k] for k in ['skill_name','skill_type','importance']) for r in links))
    for name in ['skill_taxonomy.csv','skill_taxonomy_lineage.csv','skill_aliases.csv']:
        now=read(ROOT/'01_TABLES'/name)
        before=[r for r in read(OLD/'01_TABLES'/name) if r['skill_id'] in skills]
        check(name+' is an exact source row subset',now==before)

    rv=np.load(ROOT/'05_MODEL_ARTIFACTS/D11_role_embeddings.npy')
    ri=read(ROOT/'05_MODEL_ARTIFACTS/D11_role_embedding_index.csv')
    check('Role embedding matrix: 655 x 384, finite, normalized, indexed',rv.shape==(655,384) and np.isfinite(rv).all() and np.allclose(np.linalg.norm(rv,axis=1),1,atol=1e-5) and [r['role_id'] for r in ri]==[r['role_id'] for r in roles] and [int(r['embedding_index']) for r in ri]==list(range(655)))
    check('Role CSV embeddings equal NPY rows',np.allclose(np.array([json.loads(r['role_embedding_384']) for r in roles]),rv,atol=1e-8))
    sv=np.load(ROOT/'05_MODEL_ARTIFACTS/D13_skill_embeddings.npy');si=read(ROOT/'05_MODEL_ARTIFACTS/D13_skill_embedding_index.csv')
    oldsi=read(OLD/'05_MODEL_ARTIFACTS/D13_skill_embedding_index.csv');oldsv=np.load(OLD/'05_MODEL_ARTIFACTS/D13_skill_embeddings.npy')
    selected=[int(r['embedding_index']) for r in oldsi if r['skill_id'] in skills]
    check('Skill embedding matrix is exact unchanged source subset',sv.shape==(6051,384) and np.array_equal(sv,oldsv[selected]) and [r['skill_id'] for r in si]==[r['skill_id'] for r in oldsi if r['skill_id'] in skills] and [int(r['embedding_index']) for r in si]==list(range(6051)))
    txb={r['skill_id']:r for r in tx}
    check('Skill CSV embedding matches indexed NPY',np.allclose(np.array([json.loads(txb[r['skill_id']]['embedding']) for r in si]),sv,atol=1e-7))

    manifest=json.loads((ROOT/'00_SOURCE_SNAPSHOT/source_manifest.json').read_text())
    check('All previous D13 source tables remain unchanged',all(sha(OLD/'01_TABLES'/name)==digest for name,digest in manifest['prior_D13']['tables_sha256'].items()))
    check('Source snapshots match recorded hashes',all(sha(ROOT/'00_SOURCE_SNAPSHOT'/name)==digest for name,digest in manifest['snapshots'].items()))
    check('Official PDF unchanged',sha(Path(manifest['MASCO2020_pdf']['local_source']))==manifest['MASCO2020_pdf']['sha256'])
    checks_artifact=json.loads((ROOT/'02_QA/artifact_authoring_checks.json').read_text())
    check('All 22 CSV matrices round-trip through artifact workbook authoring',len(checks_artifact)==22 and all(x['round_trip']=='PASS' for x in checks_artifact))
    formula=json.loads((ROOT/'02_QA/workbook_formula_check.json').read_text())
    check('Review workbook formula totals reconcile',formula['counts']==[657,638,19,18,1,655,655])
    xlsx=ROOT.parent/'outputs/01a047e7-ceba-7df3-8d1a-ba8071e66430/MASCO2020_STEM_Review.xlsx'
    ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(xlsx) as z:
        check('XLSX archive integrity',z.testzip() is None)
        sheet=ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
        values=[float(sheet.find(f'.//s:c[@r="B{r}"]/s:v',ns).text) for r in range(5,12)]
        check('Saved XLSX caches all summary counts correctly',values==formula['counts'])
        errors=[]
        for name in z.namelist():
            if re.fullmatch(r'xl/worksheets/sheet\d+\.xml',name):
                xml=ET.fromstring(z.read(name))
                errors += [(name,c.attrib['r']) for c in xml.findall('.//s:c[@t="e"]',ns)]
        check('No saved Excel error cells',not errors)
    sql=json.loads((ROOT/'02_QA/sql_validation.json').read_text())
    check('SQL import matches counts and is not a current database migration',sql['insert_rows']=={'roles':655,'skill_taxonomy':6051,'skill_aliases':37521,'role_skills':41286,'role_skill_lineage':41286} and sql['target_database']=='rerouteher_masco2020_test' and sql['live_database_executed'] is False and sql['schema_changed'] is False)
    check('SQL checksum matches',sha(ROOT/'04_DATABASE/MASCO2020_LOAD_EMPTY_TEST_SCHEMA.sql')==sql['sql_sha256'])
    report={'result':'PASS','checks_passed':len(checks),'checks':checks,'limits':['Project-reviewed crosswalk, not an official MASCO version crosswalk.','Functional matches and inherited task profiles need human validation before production.','SQL structurally validated, not executed against a database.']}
    (ROOT/'02_QA/validation_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'result':'PASS','checks_passed':len(checks)},indent=2))

if __name__=='__main__':validate()
