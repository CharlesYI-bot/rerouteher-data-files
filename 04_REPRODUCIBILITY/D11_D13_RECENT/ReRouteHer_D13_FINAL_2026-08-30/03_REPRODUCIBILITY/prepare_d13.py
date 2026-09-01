#!/usr/bin/env python3
"""NLP/data preparation. JSON matrices are authored as CSV by author_tables.mjs.

No claim of official MASCO-to-ESCO equivalence is made. All primary assignments
are project mappings; partial proxies remain prominently flagged for review.
"""
from pathlib import Path
from collections import Counter, defaultdict
from difflib import SequenceMatcher
import csv, hashlib, json, re, shutil, unicodedata
import numpy as np
from sentence_transformers import SentenceTransformer
from mapping_decisions import overrides

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT.parent/'ReRouteHer_D13_ESCO_LeafSkills_D11_2026-08-29'
D11=ROOT.parent/'ReRouteHer_D11_STEM_2026-08-29/01_TABLES/D11_STEM_roles.csv'
SRC=ROOT/'00_SOURCE_SNAPSHOT'
QA=ROOT/'02_QA'
MODEL='sentence-transformers/all-MiniLM-L6-v2'

def read(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def jsave(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(s):
    s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
    return ' '.join(re.findall(r'[a-z0-9]+',s))
def latest(rows):
    d={}
    for r in rows:
        if r['conceptUri'] not in d or r['modifiedDate']>d[r['conceptUri']]['modifiedDate']:d[r['conceptUri']]=r
    return list(d.values())
def sid(uri):return uri.rstrip('/').split('/')[-1]
def typ(s):return s['skillType'] or ('esco_unspecified_digcomp' if 'concept-scheme/digcomp' in s['inScheme'] else 'esco_unspecified')

def main():
    for sub in ['00_SOURCE_SNAPSHOT','01_TABLES','02_QA','05_MODEL_ARTIFACTS']:(ROOT/sub).mkdir(parents=True,exist_ok=True)
    original=OLD/'00_SOURCE_SNAPSHOT/ESCO_v1.2.1_classification_en_csv'
    es=SRC/'ESCO_v1.2.1_classification_en_csv';es.mkdir(exist_ok=True)
    manifest=[]
    for name in ['occupations_en.csv','skills_en.csv','occupationSkillRelations_en.csv']:
        shutil.copy2(original/name,es/name)
        manifest.append({'file':'00_SOURCE_SNAPSHOT/ESCO_v1.2.1_classification_en_csv/'+name,'sha256':sha(es/name),'authority':'European Commission ESCO v1.2.1','source_url':'https://esco.ec.europa.eu/en/use-esco/download','rows':len(read(es/name))})
    shutil.copy2(D11,SRC/'D11_STEM_roles.csv')
    manifest.append({'file':'00_SOURCE_SNAPSHOT/D11_STEM_roles.csv','sha256':sha(D11),'authority':'User-selected D11 2026-08-29; eMASCO-derived profiles','source_url':'https://emasco.mohr.gov.my','rows':657})
    roles=read(D11); occ=latest(read(es/'occupations_en.csv')); skills=latest(read(es/'skills_en.csv'));rels=read(es/'occupationSkillRelations_en.csv')
    bycode={o['code']:o for o in occ};byskill={s['conceptUri']:s for s in skills}
    candidates=json.loads((QA/'candidate_review.json').read_text());byrole={r['role_id']:r for r in candidates}
    prefs=defaultdict(list)
    for o in occ:prefs[norm(o['preferredLabel'])].append(o)
    curated=overrides();assert not set(curated)-{r['masco_code'] for r in roles}
    assert not {d['code'] for d in curated.values()}-set(bycode)
    relation_names={'c':'close_match','b':'broader_proxy','p':'partial_proxy'}
    coverage=[];review=[];evidence=[];candidate_rows=[];changes=[];source_issues=[]
    for r in roles:
        cr=byrole[r['role_id']];title=cr['cleaned_title'];nt=norm(title)
        pref=prefs[nt]
        decision=curated.get(r['masco_code'])
        if decision:
            o=bycode[decision['code']];rel=relation_names[decision['relation']]
            method='curated_title_and_duty_decision';reason=decision['rationale']
        else:
            o=pref[0] if len(pref)==1 else bycode[cr['old_esco_code'] or cr['candidates'][0]['code']]
            exact_alias=nt in [norm(x) for x in o['altLabels'].splitlines()]
            rel='close_match' if len(pref)==1 or exact_alias else 'partial_proxy'
            method='unique_cleaned_preferred_label' if len(pref)==1 else 'reviewed_existing_or_retrieved_candidate'
            reason=('Preferred occupation title matches after removing Malaysian grade/competency wrappers.' if len(pref)==1 else
                    'ESCO alternate title matches the cleaned MASCO title; national qualifications and full task scope are not assumed equivalent.' if exact_alias else
                    'Title/duty comparison supports this primary proxy, but occupational breadth, specialisation or seniority may differ. See both source profiles in the evidence table.')
        alignment='exact_preferred_label' if nt==norm(o['preferredLabel']) else 'exact_alternate_label' if nt in [norm(x) for x in o['altLabels'].splitlines()] else 'non_exact_title'
        confidence='high' if rel=='close_match' and alignment=='exact_preferred_label' else 'medium' if rel!='partial_proxy' else 'low'
        issue=''
        if r['masco_code']=='131103':issue='D11 task_summary describes turf maintenance whereas the title/description concerns veterinary management. Mapping uses title and description only.'
        if r['masco_code']=='311510':issue='D11 competent-person hygiene profile combines exposure assessment and routine cleaning; competent-person duty scope requires checking.'
        if r['masco_code']=='214104':issue='D11 communication-analyst profile describes corporate communications despite engineering-group placement. Mapping follows supplied duties; verify source classification.'
        if issue:source_issues.append({'role_id':r['role_id'],'masco_code':r['masco_code'],'role_title':r['role_title'],'issue':issue,'action':'Source preserved; uncertain duty scope flagged, not silently repaired.','source_url':r['source_url']})
        labels=[('preferred',o['preferredLabel'])]+[('alternate',x) for x in o['altLabels'].splitlines() if x]
        label_type,label=max(labels,key=lambda z:SequenceMatcher(None,nt,norm(z[1])).ratio())
        score=SequenceMatcher(None,nt,norm(label)).ratio()
        selected_candidate=next((c for c in cr['candidates'] if c['code']==o['code']),{})
        common={'role_id':r['role_id'],'role_title':r['role_title'],'masco_code':r['masco_code'],'masco_unit_group_code':r['masco_unit_group_code'],
            'chosen_esco_code':o['code'],'chosen_esco_title':o['preferredLabel'],'chosen_esco_uri':o['conceptUri'],
            'mapping_relation':rel,'mapping_confidence':confidence,'mapping_rationale':reason,
            'review_status':'assistant_drafted_pending_domain_validation','production_ready':'False'}
        cov={**common,'masco_code_printed':r['masco_code_printed'],'chosen_esco_isco_group':o['iscoGroup'],
            'd11_esco_code':r['esco_code'],'d11_esco_comparison_codes':r.get('esco_comparison_codes',''),
            'd11_esco_comparison_titles':r.get('esco_comparison_titles',''),
            'previous_d13_esco_code':cr['old_esco_code'],'previous_d13_mapping_status':cr['old_status'],
            'change_type':'new_mapping' if not cr['old_esco_code'] else 'corrected_mapping' if cr['old_esco_code']!=o['code'] else 'retained_mapping',
            'mapping_status':'project_'+rel,'mapping_method':method,
            'mapping_authority':'ReRouteHer project-derived; NOT an official MASCO-ESCO crosswalk',
            'title_match_type':alignment,'title_match_score':round(score,6),'score_interpretation':'Lexical similarity, not probability or equivalence confidence',
            'same_four_digit_group':str(r['masco_unit_group_code']==o['iscoGroup']),
            'use_in_role_skills':'True','specialty_skills_complete':'Not established',
            'coverage_note':'ESCO skills inherited from one primary occupation. Essential/optional refers to ESCO, not a verified Malaysian requirement.',
            'source_quality_flag':issue,'masco_source_url':r['source_url'],'esco_source_url':o['conceptUri']}
        coverage.append(cov)
        review.append({**common,'priority':'high' if confidence=='low' or issue else 'normal','review_decision':'','reviewer':'','review_date':'','review_notes':'','masco_source_url':r['source_url'],'esco_source_url':o['conceptUri']})
        evidence.append({**common,'cleaned_masco_title':title,'masco_description':r['occupation_description'],'masco_tasks':r['task_summary'],
            'esco_description':o['description'],'esco_alternate_labels':o['altLabels'],
            'matched_esco_label':label,'matched_label_type':label_type,
            'retrieval_score':selected_candidate.get('score',''),'retrieval_score_is_probability':'False',
            'source_quality_flag':issue,'masco_source_url':r['source_url'],'esco_source_url':o['conceptUri']})
        if cov['change_type']=='corrected_mapping':changes.append({'role_id':r['role_id'],'masco_code':r['masco_code'],'role_title':r['role_title'],'previous_esco_code':cr['old_esco_code'],'previous_esco_title':bycode[cr['old_esco_code']]['preferredLabel'],'chosen_esco_code':o['code'],'chosen_esco_title':o['preferredLabel'],'rationale':reason})
        for rank,c in enumerate(cr['candidates'],1):
            candidate_rows.append({'role_id':r['role_id'],'masco_code':r['masco_code'],'role_title':r['role_title'],'candidate_rank':rank,
                'candidate_esco_code':c['code'],'candidate_esco_title':c['title'],'candidate_esco_uri':c['uri'],
                'retrieval_score':c['score'],'title_cosine':c['title_cosine'],'profile_cosine':c['profile_cosine'],
                'same_four_digit_group':str(c['same_group']),'selected_primary':str(c['code']==o['code']),
                'status':'selected' if c['code']==o['code'] else 'alternative_not_used','score_is_probability':'False'})
    covby={r['role_id']:r for r in coverage}
    relby=defaultdict(list)
    for r in rels:
        assert r['relationType'] in {'essential','optional'}
        relby[r['occupationUri']].append(r)
    scoped_uris={r['skillUri'] for c in coverage for r in relby[c['chosen_esco_uri']]}
    scoped=sorted((byskill[u] for u in scoped_uris),key=lambda s:(s['preferredLabel'].casefold(),s['conceptUri']))
    inputs=[s['preferredLabel']+'. '+(s['definition'].strip() or s['description'].strip()) for s in scoped]
    model=SentenceTransformer(MODEL,local_files_only=True,device='cpu')
    vectors=model.encode(inputs,batch_size=64,normalize_embeddings=True,show_progress_bar=True).astype(np.float32)
    np.save(ROOT/'05_MODEL_ARTIFACTS/D13_skill_embeddings.npy',vectors)
    taxonomy=[];sl=[];aliases=[];seen=set()
    curated_aliases={'use spreadsheets software':['Excel','MS Excel','spreadsheets'],'JavaScript':['JS','Java Script'],'SQL':['Structured Query Language']}
    for i,(s,v) in enumerate(zip(scoped,vectors)):
        sk=sid(s['conceptUri']);definition=s['definition'].strip() or s['description'].strip()
        taxonomy.append({'skill_id':sk,'canonical_name':s['preferredLabel'],'definition':definition,'skill_type':typ(s),'embedding':'['+','.join(f'{float(x):.8f}' for x in v)+']'})
        sl.append({'skill_id':sk,'concept_uri':s['conceptUri'],'preferred_label':s['preferredLabel'],'skill_type':typ(s),'official_skill_type_raw':s['skillType'],
            'reuse_level':s['reuseLevel'],'status':s['status'],'modified_date':s['modifiedDate'],'definition_source_field':'definition' if s['definition'].strip() else 'description',
            'embedding_text':inputs[i],'embedding_model':MODEL,'embedding_dimensions':384,'l2_normalized':'True','source_version':'ESCO v1.2.1'})
        for source,ls in [('esco_altLabel',s['altLabels'].splitlines()),('esco_hiddenLabel',s['hiddenLabels'].splitlines()),('curated_product_or_acronym',curated_aliases.get(s['preferredLabel'],[]))]:
            for label in ls:
                label=' '.join(label.split());key=(sk,label.casefold())
                if not label or label.casefold()==s['preferredLabel'].casefold() or key in seen:continue
                seen.add(key);aliases.append({'skill_id':sk,'alias':label,'alias_source':source})
    aliases.sort(key=lambda x:(x['skill_id'],x['alias'].casefold()))
    rs=[];rsl=[]
    for c in coverage:
        for r in sorted(relby[c['chosen_esco_uri']],key=lambda r:r['skillUri']):
            s=byskill[r['skillUri']]
            base={'role_id':c['role_id'],'skill_id':sid(r['skillUri']),'skill_name':s['preferredLabel'],'skill_type':typ(s),'importance':100 if r['relationType']=='essential' else 50}
            rs.append(base)
            rsl.append({**base,'masco_code':c['masco_code'],'esco_code':c['chosen_esco_code'],'esco_occupation_title':c['chosen_esco_title'],'esco_occupation_uri':c['chosen_esco_uri'],
                'skill_uri':r['skillUri'],'relation_type':r['relationType'],'mapping_relation':c['mapping_relation'],'mapping_confidence':c['mapping_confidence'],
                'mapping_review_status':c['review_status'],'source_version':'ESCO v1.2.1','production_ready':'False'})
    summary={'release_date':'2026-08-30','d11_role_count':len(roles),'six_digit_masco_role_count':sum(bool(re.fullmatch(r'\d{6}',r['masco_code'])) for r in roles),
        'roles_with_project_esco_mapping':len(coverage),'previous_mapped_roles':sum(bool(r['old_esco_code']) for r in candidates),
        'newly_mapped_roles':sum(c['change_type']=='new_mapping' for c in coverage),'corrected_previous_mappings':len(changes),
        'roles_without_primary_mapping':sum(not c['chosen_esco_code'] for c in coverage),'roles_with_skill_links':len({r['role_id'] for r in rs}),
        'distinct_esco_occupations_used':len({c['chosen_esco_uri'] for c in coverage}),
        'mapping_relation_counts':dict(Counter(c['mapping_relation'] for c in coverage)),'mapping_confidence_counts':dict(Counter(c['mapping_confidence'] for c in coverage)),
        'curated_decisions':len(curated),'scoped_leaf_skills':len(scoped),'skill_alias_rows':len(aliases),'role_skill_rows':len(rs),
        'essential_role_skill_rows':sum(r['importance']==100 for r in rs),'optional_role_skill_rows':sum(r['importance']==50 for r in rs),
        'source_quality_flags':len(source_issues),'embedding_model':MODEL,'embedding_dimensions':384,'l2_normalized':True,
        'human_validated_mappings':0,'official_crosswalk':False,'deployed':False,
        'coverage_interpretation':'657 assigned primary occupations includes broader and partial proxies; not 657 exact equivalents or complete specialty profiles.',
        'qualification_warning':'ESCO skill inheritance does not establish Malaysian licences, protected titles, competency certification, remote-work feasibility or specialty completeness.'}
    jsave(QA/'D13_build_summary.json',summary)
    jsave(ROOT/'05_MODEL_ARTIFACTS/D13_embedding_model.json',{'model':MODEL,'dimensions':384,'l2_normalized':True,'skill_count':len(scoped),'input_format':'preferredLabel + period + definition, fallback description','min_l2_norm':float(np.linalg.norm(vectors,axis=1).min()),'max_l2_norm':float(np.linalg.norm(vectors,axis=1).max())})
    tables={}
    def table(path,rows):
        assert rows,path
        cols=list(rows[0]);assert all(set(r)==set(cols) for r in rows),path
        tables[path]={'columns':cols,'rows':[[r[k] for k in cols] for r in rows]}
    table('01_TABLES/D13_role_esco_coverage.csv',coverage)
    table('01_TABLES/D13_role_esco_mapping_review.csv',review)
    table('01_TABLES/D13_mapping_evidence.csv',evidence)
    table('01_TABLES/D13_mapping_candidates.csv',candidate_rows)
    table('01_TABLES/skill_taxonomy.csv',taxonomy)
    table('01_TABLES/skill_taxonomy_lineage.csv',sl)
    table('01_TABLES/skill_aliases.csv',aliases)
    table('01_TABLES/role_skills.csv',rs)
    table('01_TABLES/role_skills_lineage.csv',rsl)
    table('02_QA/D13_corrected_previous_mappings.csv',changes)
    table('02_QA/D13_source_quality_issues.csv',source_issues)
    table('02_QA/D13_source_manifest.csv',manifest)
    table('05_MODEL_ARTIFACTS/D13_skill_embedding_index.csv',[{'embedding_index':i,'skill_id':sid(s['conceptUri'])} for i,s in enumerate(scoped)])
    jsave(QA/'table_payloads.json',tables)
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
