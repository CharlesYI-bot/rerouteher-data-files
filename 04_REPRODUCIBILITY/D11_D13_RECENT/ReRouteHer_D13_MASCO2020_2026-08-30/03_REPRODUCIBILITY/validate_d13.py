"""Validate the reconstructed joins, Title Case, source lineage and artifacts."""
import json,re,collections,zipfile,xml.etree.ElementTree as ET
import numpy as np
from common import ROOT,STEM,PRIOR,ESCO,read,latest,sha,norm,MODEL
from label_case import title_case,match_alias,self_test
from mapping_decisions_2020 import DECISIONS

def main():
    checks=[]
    def check(name,ok,detail=''):
        assert ok,(name,detail)
        checks.append({'check':name,'result':'PASS','detail':detail})
    def unique(rows,*keys):return len(rows)==len({tuple(r[k] for k in keys) for r in rows})
    summary=json.loads((ROOT/'02_QA/D13_build_summary.json').read_text())
    protected=json.loads((ROOT/'03_REPRODUCIBILITY/title_case_policy.json').read_text())['protected_spellings']
    roles=read(ROOT/'01_TABLES/D11_STEM_roles.csv');oldroles={r['role_id']:r for r in read(STEM/'01_TABLES/D11_STEM_roles.csv')}
    cov=read(ROOT/'01_TABLES/D13_role_esco_coverage.csv');cb={r['role_id']:r for r in cov}
    occ={r['code']:r for r in latest(read(ESCO/'occupations_en.csv'))};skills={r['conceptUri']:r for r in latest(read(ESCO/'skills_en.csv'))}
    check('Exactly the approved 655 MASCO 2020 identities',len(roles)==655 and unique(roles,'role_id') and set(cb)==set(oldroles)=={r['role_id'] for r in roles})
    check('Role IDs use six-digit occupation codes',all(re.fullmatch(r'\d{6}',r['masco_code']) and r['role_id']=='M'+r['masco_code'] for r in roles))
    check('D1-compatible first 24 role columns preserved',list(roles[0])[:24]==list(next(iter(oldroles.values())))[:24])
    check('MASCO titles, tasks, ratings and other non-ESCO fields unchanged',all(all(r[k]==oldroles[r['role_id']][k] for k in oldroles[r['role_id']] if 'esco' not in k.lower()) for r in roles))
    check('MASCO 2020 source role CSV snapshot unchanged',sha(ROOT/'00_SOURCE_SNAPSHOT/D11_MASCO2020_STEM_roles.csv')==sha(STEM/'01_TABLES/D11_STEM_roles.csv'))
    check('Every ESCO code/URI resolves to official source',all(c['chosen_esco_code'] in occ and c['chosen_esco_uri']==occ[c['chosen_esco_code']]['conceptUri'] for c in cov))
    check('Every chosen ESCO title uses the Title Case official preferred label',all(c['chosen_esco_title']==title_case(occ[c['chosen_esco_code']]['preferredLabel'],protected) for c in cov))
    check('D11 ESCO code and display title agree with D13',all(r['esco_code']==cb[r['role_id']]['chosen_esco_code'] and r['esco_title']==cb[r['role_id']]['chosen_esco_title'] for r in roles))
    check('All 65 explicit 2020 target decisions applied',len(DECISIONS)==65 and all(cb['M'+k]['chosen_esco_code']==v['code'] and cb['M'+k]['mapping_relation']==v['relation'] for k,v in DECISIONS.items()))
    for name in ['D13_mapping_evidence.csv','D13_role_esco_mapping_review.csv']:
        rows=read(ROOT/'01_TABLES'/name)
        check(name+' agrees with primary coverage',len(rows)==655 and unique(rows,'role_id') and all(r['chosen_esco_code']==cb[r['role_id']]['chosen_esco_code'] and r['chosen_esco_title']==cb[r['role_id']]['chosen_esco_title'] for r in rows))
    check('No production-ready or false human-review claims',all(c['production_ready']=='false' and c['review_status']=='test_only_project_mapping_not_human_validated' for c in cov))
    fresh=json.loads((ROOT/'02_QA/retrieval_metadata.json').read_text())
    candidates=read(ROOT/'01_TABLES/D13_mapping_candidates.csv');selected=[r for r in candidates if r['selected_primary']=='true']
    check('Fresh 2020 queries for all roles; numeric group not used to rank',fresh['role_count']==655 and fresh['masco_isco_numeric_prefix_used_in_ranking'] is False and all(r['query_masco_version']=='2020' for r in candidates))
    check('Exactly one selected fresh candidate per role',len(selected)==655 and unique(selected,'role_id') and all(r['candidate_esco_code']==cb[r['role_id']]['chosen_esco_code'] for r in selected))
    check('Known misleading aliases not adopted',cb['M221211']['chosen_esco_code']=='2212.1' and cb['M818209']['chosen_esco_code']!='8311.1' and cb['M254209']['chosen_esco_code']!='2651.5')
    changed=read(ROOT/'02_QA/D13_mapping_changes.csv')
    check('Mapping changes reconcile',len(changed)==655 and sum(r['esco_code_changed']=='true' for r in changed)==summary['changed_primary_esco_codes']==16)

    tx=read(ROOT/'01_TABLES/skill_taxonomy.csv');sl=read(ROOT/'01_TABLES/skill_taxonomy_lineage.csv');tb={r['skill_id']:r for r in tx};lb={r['skill_id']:r for r in sl}
    links=read(ROOT/'01_TABLES/role_skills.csv');lineage=read(ROOT/'01_TABLES/role_skills_lineage.csv')
    rels=read(ESCO/'occupationSkillRelations_en.csv');relby=collections.defaultdict(dict)
    for r in rels:relby[r['occupationUri']][r['skillUri']]=r['relationType']
    expected={(c['role_id'],uri.rsplit('/',1)[-1]):(uri,rel) for c in cov for uri,rel in relby[c['chosen_esco_uri']].items()}
    actual={(r['role_id'],r['skill_id']):r for r in links}
    check('Role-skill links are exactly the official essential/optional join',len(links)==len(actual)==len(expected)==summary['role_skill_rows'] and set(actual)==set(expected))
    check('No orphan role or skill keys',all(r['role_id'] in cb and r['skill_id'] in tb for r in links) and set(tb)=={r['skill_id'] for r in links})
    check('Every role has skill links; skill scope is not full ESCO universe',len({r['role_id'] for r in links})==655 and len(tx)==len(tb)==len(sl)==summary['scoped_leaf_skills'] and len(tx)<len(skills))
    check('Importance exactly essential=100, optional=50',all(int(actual[key]['importance'])==(100 if rel=='essential' else 50) for key,(uri,rel) in expected.items()))
    check('Skill names/types agree in all link records',all(r['skill_name']==tb[r['skill_id']]['canonical_name'] and r['skill_type']==tb[r['skill_id']]['skill_type'] for r in links+lineage))
    check('Role-skill lineage has one exact row per link',len(lineage)==len(links) and unique(lineage,'role_id','skill_id') and {(r['role_id'],r['skill_id']) for r in lineage}==set(actual) and all(r['esco_code']==cb[r['role_id']]['chosen_esco_code'] and r['esco_occupation_title']==cb[r['role_id']]['chosen_esco_title'] for r in lineage))
    check('Canonical skills are Title Case preferred labels',all(tb[r['skill_id']]['canonical_name']==r['preferred_label']==title_case(skills[r['concept_uri']]['preferredLabel'],protected) for r in sl))
    check('Raw preferred labels/types retained exactly in lineage',all(r['preferred_label_raw']==skills[r['concept_uri']]['preferredLabel'] and r['official_skill_type_raw']==skills[r['concept_uri']]['skillType'] for r in sl))
    check('Definitions use unchanged ESCO description, then definition fallback',all(tb[r['skill_id']]['definition']==(skills[r['concept_uri']]['description'].strip() or skills[r['concept_uri']]['definition'].strip()) for r in sl))
    check('Skill categories fit unchanged existing schema',set(r['skill_type'] for r in tx)<={'technical','soft','digital'} and dict(collections.Counter(r['skill_type'] for r in tx))==summary['skill_type_counts'])
    aliases=read(ROOT/'01_TABLES/skill_aliases.csv');al=read(ROOT/'01_TABLES/skill_aliases_lineage.csv')
    check('Aliases unique, lowercase and not duplicate canonical matches',len(aliases)==summary['skill_alias_rows'] and unique(aliases,'skill_id','alias') and all(r['skill_id'] in tb and r['alias']==match_alias(r['alias']) and r['alias']!=match_alias(tb[r['skill_id']]['canonical_name']) for r in aliases))
    check('Alias provenance and display casing agree with raw labels',len(al)==len(aliases) and {(r['skill_id'],r['alias']) for r in al}=={(r['skill_id'],r['alias']) for r in aliases} and all(r['alias_display_title']==title_case(json.loads(r['raw_labels_json'])[0],protected) and all(match_alias(x)==r['alias'] for x in json.loads(r['raw_labels_json'])) for r in al))
    # Independently reconstruct required raw aliases to prove none were lost.
    expected_aliases=set()
    for r in sl:
        s=skills[r['concept_uri']]
        for raw in (s['altLabels']+'\n'+s['hiddenLabels']).splitlines():
            a=match_alias(raw)
            if a and a!=match_alias(s['preferredLabel']):expected_aliases.add((r['skill_id'],a))
    check('All official alternate/hidden matching aliases preserved',expected_aliases<={(r['skill_id'],r['alias']) for r in aliases})
    original=read(STEM/'01_TABLES/ESCO_comparison_preservation.csv');comparison=read(ROOT/'01_TABLES/ESCO_comparison_preservation.csv')
    check('657 original comparison records preserved: identifiers exact, titles recased only',len(comparison)==657 and all(all(a[k]==(title_case(b[k],protected) if 'esco' in k and 'title' in k else b[k]) for k in b) for a,b in zip(comparison,original)))

    case_audit=read(ROOT/'02_QA/D13_title_case_audit.csv')
    check('Every audited display label follows the case policy',len(case_audit)==summary['title_case_unique_audit_labels'] and all(r['title_case_label']==title_case(r['raw_label'],protected) and title_case(r['title_case_label'],protected)==r['title_case_label'] for r in case_audit))
    check('Casing does not alter label wording or punctuation',all(' '.join(r['raw_label'].split()).casefold()==' '.join(r['title_case_label'].split()).casefold() for r in case_audit))
    display_cells=0
    for p in list((ROOT/'01_TABLES').glob('*.csv'))+list((ROOT/'02_QA').glob('*.csv')):
        for r in read(p):
            for key,value in r.items():
                is_display=('esco' in key.lower() and ('title' in key.lower() or 'label' in key.lower())) or key in {'canonical_name','skill_name','preferred_label','alias_display_title','title_case_label'}
                if is_display and 'raw' not in key.lower() and value:
                    assert value==title_case(value,protected),(p.name,key,value)
                    display_cells+=1
    check('All operational ESCO display fields consistently Title Cased',display_cells>50000,str(display_cells)+' nonempty display cells checked')
    check('21 acronym/product/ordinary-word case regression tests pass',self_test(protected)==summary['title_case_unit_tests_passed']==21)

    v=np.load(ROOT/'05_MODEL_ARTIFACTS/D13_skill_embeddings.npy');index=read(ROOT/'05_MODEL_ARTIFACTS/D13_skill_embedding_index.csv')
    check('Skill matrix shape, finite values, normalization and index',v.shape==(len(tx),384) and np.isfinite(v).all() and np.allclose(np.linalg.norm(v,axis=1),1,atol=1e-5) and [r['skill_id'] for r in index]==[r['skill_id'] for r in tx] and [int(r['embedding_index']) for r in index]==list(range(len(tx))))
    check('CSV vectors agree with NPY matrix',np.allclose(v,np.array([json.loads(r['embedding']) for r in tx]),atol=1e-8))
    check('Embedding text matches corrected display name plus source definition',all(r['embedding_text']==tb[r['skill_id']]['canonical_name']+'. '+tb[r['skill_id']]['definition'] for r in sl))
    from sentence_transformers import SentenceTransformer
    model=SentenceTransformer(MODEL,local_files_only=True,device='cpu')
    ix=sorted({0,len(sl)//2,len(sl)-1}|{i for i,r in enumerate(sl) if r['preferred_label'] in ['JavaScript','SQL','Use Spreadsheets Software']})
    sample=model.encode([sl[i]['embedding_text'] for i in ix],normalize_embeddings=True,show_progress_bar=False)
    check('Independent embedding recomputation spot-check',np.allclose(v[ix],sample,atol=2e-6),str(len(ix))+' exact input samples')
    check('D11 role embeddings/index retained unchanged',all(sha(ROOT/'05_MODEL_ARTIFACTS'/name)==sha(STEM/'05_MODEL_ARTIFACTS'/name) for name in ['D11_role_embeddings.npy','D11_role_embedding_index.csv']))
    check('Raw ESCO snapshots unchanged',all(sha(ROOT/'00_SOURCE_SNAPSHOT/ESCO_v1.2.1_classification_en_csv'/name)==sha(ESCO/name) for name in ['occupations_en.csv','skills_en.csv','occupationSkillRelations_en.csv']))
    check('All source manifest hashes match',all(sha(ROOT/r['file'])==r['sha256'] for r in read(ROOT/'02_QA/D13_source_manifest.csv')))
    authored=json.loads((ROOT/'02_QA/artifact_authoring_checks.json').read_text())
    check('19 complete CSV matrices round-trip checked through artifact authoring',len(authored)==19 and all(x['round_trip']=='PASS' for x in authored))
    sql=json.loads((ROOT/'02_QA/sql_validation.json').read_text())
    check('SQL is guarded for a separate empty test database and correct row counts',sql['target_database']=='rerouteher_masco2020_test' and sql['schema_changed'] is False and sql['live_database_executed'] is False and sql['insert_rows']['roles']==655 and sql['insert_rows']['skill_taxonomy']==len(tx) and sql['insert_rows']['role_skills']==len(links))
    check('SQL checksum matches',sha(ROOT/'04_DATABASE/MASCO2020_LOAD_EMPTY_TEST_SCHEMA.sql')==sql['sql_sha256'])
    wb=json.loads((ROOT/'02_QA/workbook_checks.json').read_text())
    check('Review workbook formula totals reconcile',wb['counts']==wb['expected'])
    xlsx=ROOT.parent/'outputs/01a047e7-ceba-7df3-8d1a-ba8071e66430/D13_MASCO2020_TitleCase_Review.xlsx'
    ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(xlsx) as z:
        check('Review workbook ZIP integrity',z.testzip() is None)
        first=ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
        saved=[float(first.find(f'.//m:c[@r="B{i}"]/m:v',ns).text) for i in range(5,14)]
        check('Saved workbook formula caches match expected counts',saved==wb['expected'])
        errors=[]
        for p in z.namelist():
            if re.fullmatch(r'xl/worksheets/sheet\d+\.xml',p):errors.extend(ET.fromstring(z.read(p)).findall('.//m:c[@t="e"]',ns))
        check('No Excel error cells in saved workbook',not errors)
    report={'result':'PASS','checks_passed':len(checks),'checks':checks,
        'limits':['Mappings are project test proxies, not an official crosswalk or independently human-validated.',
                  'SQL was structurally checked but not executed against a database.','Raw source labels and lowercase matching aliases intentionally retain non-Title-Case forms.']}
    (ROOT/'02_QA/D13_validation_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'result':'PASS','checks_passed':len(checks),'display_cells_checked':display_cells},indent=2))

if __name__=='__main__':main()
