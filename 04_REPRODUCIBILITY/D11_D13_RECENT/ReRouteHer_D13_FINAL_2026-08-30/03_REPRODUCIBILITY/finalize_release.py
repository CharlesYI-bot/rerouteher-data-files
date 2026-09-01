"""Fast structural/source validation, test SQL generation, checksums and ZIP."""
from pathlib import Path
from collections import Counter
import csv, hashlib, json, re, zipfile
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
def read(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def latest(rows):
    d={}
    for r in rows:
        if r['conceptUri'] not in d or r['modifiedDate']>d[r['conceptUri']]['modifiedDate']:d[r['conceptUri']]=r
    return d
def save(p,obj):p.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n')

def main():
    t=ROOT/'01_TABLES';qa=ROOT/'02_QA';src=ROOT/'00_SOURCE_SNAPSHOT';es=src/'ESCO_v1.2.1_classification_en_csv'
    c=read(t/'D13_role_esco_coverage.csv');tx=read(t/'skill_taxonomy.csv');al=read(t/'skill_aliases.csv');rs=read(t/'role_skills.csv');ln=read(t/'role_skills_lineage.csv')
    roles=read(src/'D11_STEM_roles.csv');cb={x['role_id']:x for x in c};sb={x['skill_id']:x for x in tx}
    occ=latest(read(es/'occupations_en.csv'));ob={r['code']:r for r in occ.values()}
    officialskills=latest(read(es/'skills_en.csv'))
    relations=read(es/'occupationSkillRelations_en.csv');rel={(r['occupationUri'],r['skillUri']):r for r in relations}
    vec=np.load(ROOT/'05_MODEL_ARTIFACTS/D13_skill_embeddings.npy');index=read(ROOT/'05_MODEL_ARTIFACTS/D13_skill_embedding_index.csv')
    checks=[]
    def check(name,ok,observed=''):checks.append({'check':name,'passed':bool(ok),'observed':observed})
    check('all_657_D11_roles_mapped_once',len(c)==657 and len(cb)==657 and set(cb)=={r['role_id'] for r in roles},len(c))
    check('562_additional_roles_mapped',sum(r['change_type']=='new_mapping' for r in c)==562)
    check('MASCO_identifiers_are_six_digits',all(re.fullmatch(r'\d{6}',r['masco_code']) and r['role_id']=='M'+r['masco_code'] for r in c))
    check('all_primary_codes_URIs_titles_exist_in_ESCO',all(r['chosen_esco_code'] in ob and (r['chosen_esco_uri'],r['chosen_esco_title'])==(ob[r['chosen_esco_code']]['conceptUri'],ob[r['chosen_esco_code']]['preferredLabel']) for r in c))
    check('original_D11_ESCO_comparison_fields_preserved',all(cb[r['role_id']]['d11_esco_code']==r['esco_code'] and cb[r['role_id']]['d11_esco_comparison_codes']==r.get('esco_comparison_codes','') for r in roles))
    check('D11_source_unchanged',sha(src/'D11_STEM_roles.csv')==sha(ROOT.parent/'ReRouteHer_D11_STEM_2026-08-29/01_TABLES/D11_STEM_roles.csv'))
    check('all_657_roles_have_skills',{r['role_id'] for r in rs}==set(cb),len({r['role_id'] for r in rs}))
    check('skill_taxonomy_unique',len(tx)==len(sb),len(tx))
    check('role_skill_pairs_unique',len(rs)==len({(r['role_id'],r['skill_id']) for r in rs}),len(rs))
    check('role_and_skill_foreign_keys',all(r['role_id'] in cb and r['skill_id'] in sb for r in rs))
    check('skill_names_and_types_match_taxonomy',all(r['skill_name']==sb[r['skill_id']]['canonical_name'] and r['skill_type']==sb[r['skill_id']]['skill_type'] for r in rs))
    check('taxonomy_only_contains_linked_leaf_skills',set(sb)=={r['skill_id'] for r in rs} and len(tx)<len(officialskills))
    check('importance_is_100_or_50',{r['importance'] for r in rs}=={'100','50'})
    check('lineage_covers_every_role_skill_pair',Counter((r['role_id'],r['skill_id']) for r in ln)==Counter((r['role_id'],r['skill_id']) for r in rs))
    check('every_role_skill_is_an_official_ESCO_relation',all((r['esco_occupation_uri'],r['skill_uri']) in rel and rel[r['esco_occupation_uri'],r['skill_uri']]['relationType']==r['relation_type'] and r['esco_occupation_uri']==cb[r['role_id']]['chosen_esco_uri'] for r in ln))
    check('importance_follows_official_relation',all(r['importance']==('100' if r['relation_type']=='essential' else '50') for r in ln))
    check('aliases_have_valid_skill_FKs',all(r['skill_id'] in sb for r in al))
    check('aliases_case_insensitive_unique_per_skill',len(al)==len({(r['skill_id'],r['alias'].casefold()) for r in al}))
    check('required_product_acronym_aliases_present',{'Excel','MS Excel','spreadsheets','JS','Structured Query Language'}<={r['alias'] for r in al})
    check('all_embeddings_384_dimensional',vec.shape==(len(tx),384),list(vec.shape))
    check('embeddings_finite_and_L2_normalized',np.isfinite(vec).all() and np.allclose(np.linalg.norm(vec,axis=1),1,atol=1e-5))
    check('embedding_index_matches_taxonomy',len(index)==len(tx) and all(r['skill_id']==tx[i]['skill_id'] and int(r['embedding_index'])==i for i,r in enumerate(index)))
    parsed=np.array([json.loads(r['embedding']) for r in tx],dtype=np.float32)
    check('CSV_vectors_match_numpy_artifact',parsed.shape==vec.shape and np.allclose(parsed,vec,atol=1e-7))
    check('mapping_evidence_and_review_cover_all_roles',all({r['role_id'] for r in read(t/name)}==set(cb) for name in ['D13_mapping_evidence.csv','D13_role_esco_mapping_review.csv']))
    check('confidence_relations_and_test_flags_explicit',all(r['mapping_confidence'] in {'high','medium','low'} and r['mapping_relation'] in {'close_match','broader_proxy','partial_proxy'} and r['production_ready']=='False' for r in c))
    manifest=read(qa/'D13_source_manifest.csv')
    check('source_snapshot_hashes_match',all(sha(ROOT/r['file'])==r['sha256'] for r in manifest))
    payload=json.loads((qa/'table_payloads.json').read_text())
    def payload_equal(name,p):
        actual=read(ROOT/name)
        if len(actual)!=len(p['rows']):return False
        return all((float(a[k])==v if isinstance(v,(int,float)) else a[k]==str(v)) for a,row in zip(actual,p['rows']) for k,v in zip(p['columns'],row))
    check('artifact_authoring_preserves_every_cell',all(payload_equal(name,p) for name,p in payload.items()))
    expected={'M243103':'2433.4','M252403':'2521.2','M254306':'2166.3.1','M431110':'4312.1','M213402':'2212.1','M291606':'5419.3'}
    check('known_misleading_title_matches_corrected',all(cb[k]['chosen_esco_code']==v for k,v in expected.items()))
    assert all(r['passed'] for r in checks),[r for r in checks if not r['passed']]
    # User explicitly requires existing structures unchanged: data-only import.
    from build_append_sql import build
    sql_report=build()
    check('append_SQL_matches_user_schema_and_has_no_DDL',sql_report['validation_passed'])
    summary=json.loads((qa/'D13_build_summary.json').read_text())
    summary.update({'intended_use':'Testing only, as explicitly requested. No production sign-off required to use this test artifact.','test_package_ready':True,'structural_checks_passed':len(checks),'database_execution_tested':False})
    save(qa/'D13_build_summary.json',summary)
    save(qa/'D13_validation_report.json',{'overall_passed':True,'checks_passed':len(checks),'checks_total':len(checks),'scope':'Source, identifiers, joins, aliases, embeddings and round-trip data integrity. Not an expert equivalence audit or live database execution.','checks':checks})
    # Do not include working JSON matrices or redundant retrieval tensors in the ZIP.
    excluded={'table_payloads.json','retrieval_vectors.npz','esco_occupation_index.json'}
    files=sorted(p for p in ROOT.rglob('*') if p.is_file() and p.name not in excluded|{'D13_OUTPUT_SHA256SUMS.txt'} and '__pycache__' not in p.parts and 'previews' not in p.parts)
    checksum=ROOT/'D13_OUTPUT_SHA256SUMS.txt'
    checksum.write_text(''.join(f'{sha(p)}  {p.relative_to(ROOT)}\n' for p in files))
    out=ROOT.parent/'outputs/01a047e7-ceba-7df3-8d1a-ba8071e66430';out.mkdir(parents=True,exist_ok=True)
    target=out/(ROOT.name+'.zip')
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files+[checksum]:z.write(p,ROOT.name+'/'+str(p.relative_to(ROOT)))
    with zipfile.ZipFile(target) as z:assert z.testzip() is None
    (out/(target.name+'.sha256')).write_text(sha(target)+'  '+target.name+'\n')
    print(json.dumps({'zip':str(target),'checks_passed':len(checks),'rows':{'roles':len(c),'skills':len(tx),'aliases':len(al),'role_skills':len(rs)},'zip_bytes':target.stat().st_size,'sha256':sha(target)},indent=2))

if __name__=='__main__':main()
