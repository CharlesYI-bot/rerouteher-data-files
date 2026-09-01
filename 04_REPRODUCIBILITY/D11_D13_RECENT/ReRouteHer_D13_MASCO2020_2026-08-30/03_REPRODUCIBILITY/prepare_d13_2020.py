"""Rebuild D13 from 655 MASCO 2020 roles and official ESCO leaf relations.

Authoring is deferred to artifact-tool: this stage prepares JSON matrices and
NumPy vectors, preserves raw sources, and documents mapping/case decisions.
"""
from collections import Counter,defaultdict
from difflib import SequenceMatcher
from pathlib import Path
import json,re,shutil
import numpy as np
from sentence_transformers import SentenceTransformer
from common import ROOT,STEM,PRIOR,ESCO,MODEL,read,save,sha,latest,norm,clean_title
from label_case import build_protected,title_case,match_alias,self_test,SMALL,TESTS
from mapping_decisions_2020 import DECISIONS,REJECT_EXACT

def main():
    for name in ['00_SOURCE_SNAPSHOT','01_TABLES','02_QA','04_DATABASE','05_MODEL_ARTIFACTS']:(ROOT/name).mkdir(parents=True,exist_ok=True)
    raw_dir=ROOT/'00_SOURCE_SNAPSHOT/ESCO_v1.2.1_classification_en_csv';raw_dir.mkdir(exist_ok=True)
    manifest=[]
    for name in ['occupations_en.csv','skills_en.csv','occupationSkillRelations_en.csv']:
        target=raw_dir/name;shutil.copy2(ESCO/name,target)
        manifest.append({'file':str(target.relative_to(ROOT)),'sha256':sha(target),'source':'European Commission ESCO v1.2.1','source_url':'https://esco.ec.europa.eu/en/use-esco/download'})
    for name,source in {
        'D11_MASCO2020_STEM_roles.csv':STEM/'01_TABLES/D11_STEM_roles.csv',
        'previous_D13_role_esco_coverage.csv':STEM/'01_TABLES/D13_role_esco_coverage.csv',
        'ESCO_comparison_preservation_raw.csv':STEM/'01_TABLES/ESCO_comparison_preservation.csv',
        'MASCO2020_role_crosswalk_raw.csv':STEM/'01_TABLES/MASCO2020_role_crosswalk.csv',
        'MASCO2020_index.csv':STEM/'00_SOURCE_SNAPSHOT/MASCO_2020_individual_occupations_en.csv',
        'user_existing_schema.sql':STEM/'00_SOURCE_SNAPSHOT/user_existing_schema.sql',
    }.items():
        target=ROOT/'00_SOURCE_SNAPSHOT'/name;shutil.copy2(source,target)
        manifest.append({'file':str(target.relative_to(ROOT)),'sha256':sha(target),'source':str(source),'source_url':''})
    brief=Path('/Users/charlesyi/Downloads/Copy of Data Team Tasks - ReRouteHer (Iteration 1).docx')
    shutil.copy2(brief,ROOT/'00_SOURCE_SNAPSHOT/D13_task_brief.docx')
    roles=read(STEM/'01_TABLES/D11_STEM_roles.csv');prior={r['role_id']:r for r in read(STEM/'01_TABLES/D13_role_esco_coverage.csv')}
    occ=latest(read(raw_dir/'occupations_en.csv'));skills=latest(read(raw_dir/'skills_en.csv'));relations=read(raw_dir/'occupationSkillRelations_en.csv')
    oc={r['code']:r for r in occ};sk={r['conceptUri']:r for r in skills};candidates={r['role_id']:r for r in json.loads((ROOT/'02_QA/candidate_review.json').read_text())}
    protected=build_protected(occ+skills);tests=self_test(protected)
    save(ROOT/'02_QA/title_case_tests.json',{'cases':[{'input':s,'expected':v,'actual':title_case(s,protected),'passed':title_case(s,protected)==v} for s,v in TESTS.items()]})
    save(ROOT/'03_REPRODUCIBILITY/title_case_policy.json',{'style':'Project English Title Case','small_words':sorted(SMALL),'protected_spellings':protected,
        'scope':'Human-readable ESCO occupation titles, canonical skill names, preferred/alternate display labels and comparison titles.',
        'exempt':'Raw source labels, descriptions/definitions, codes/IDs/URIs, lowercase matching aliases and machine enums.',
        'alias_normalization':'NFKC, collapse whitespace, lowercase; not punctuation stripping','tests_passed':tests})
    audit={}
    def display(raw,kind,ref):
        raw=str(raw or '');out=title_case(raw,protected)
        if raw:audit[(kind,ref,raw)]={'label_kind':kind,'reference':ref,'raw_label':raw,'title_case_label':out,'changed':out!=raw}
        return out
    def esco_title(code):return display(oc[code]['preferredLabel'],'occupation',oc[code]['conceptUri']) if code else ''
    def convert_comparison_columns(row):
        out=row.copy()
        for key,value in out.items():
            if 'esco' in key.lower() and 'title' in key.lower() and value:
                out[key]=display(value,'comparison',row.get('role_id',row.get('source_current_role_id',''))+'.'+key)
        return out
    code_set={r['masco_code'] for r in roles}
    assert set(DECISIONS)<=code_set and set(REJECT_EXACT)<=code_set
    assert {r['code'] for r in DECISIONS.values()}<=set(oc)
    coverage=[];evidence=[];review=[];candidate_rows=[];changes=[];alias_rejections=[]
    for role in roles:
        rid=role['role_id'];cr=candidates[rid];p=prior[rid];nt=norm(cr['cleaned_title']);d=DECISIONS.get(role['masco_code'])
        exact_pref=cr['exact_preferred_codes'];exact_any=cr['exact_label_codes']
        if d:
            chosen=d['code'];relation=d['relation'];reason=d['rationale'];method='2020_title_and_duty_review'
        elif role['masco_code'] in REJECT_EXACT:
            chosen=p['chosen_esco_code'];relation=p['source_d13_mapping_relation'];reason=REJECT_EXACT[role['masco_code']]+' Retain the earlier duty-based ESCO proxy after the fresh 2020 retrieval.';method='2020_ambiguous_alias_rejected'
        elif len(exact_pref)==1:
            chosen=exact_pref[0];relation='close_match';reason='Unique ESCO preferred title matches the MASCO 2020 title after public-service grade/competency-wrapper normalization. Qualification and full task equivalence are not assumed.';method='2020_unique_preferred_title'
        else:
            chosen=p['chosen_esco_code'];relation=p['source_d13_mapping_relation'];reason='Retained the previously curated duty-based ESCO assignment after fresh MASCO 2020 title/profile retrieval. No stronger unambiguous occupational identity was established. Prior reasoning: '+p.get('source_d13_mapping_rationale',p['mapping_rationale']);method='curated_proxy_retained_with_fresh_2020_retrieval'
        o=oc[chosen];labels=[('preferred',o['preferredLabel'])]+[('alternate',x) for x in o['altLabels'].splitlines() if x]
        kind,label=max(labels,key=lambda pair:SequenceMatcher(None,nt,norm(pair[1])).ratio())
        alignment='exact_preferred_label' if nt==norm(o['preferredLabel']) else 'exact_alternate_label' if any(nt==norm(x) for x in o['altLabels'].splitlines()) else 'non_exact_title'
        confidence='high' if relation=='close_match' and alignment=='exact_preferred_label' else 'low' if relation=='partial_proxy' else 'medium'
        assert relation in {'close_match','broader_proxy','partial_proxy'}
        new={
            'role_id':rid,'role_title':role['role_title'],'masco_code':role['masco_code'],'masco_unit_group_code':role['masco_unit_group_code'],
            'chosen_esco_code':chosen,'chosen_esco_title':esco_title(chosen),'chosen_esco_uri':o['conceptUri'],
            'mapping_relation':relation,'mapping_confidence':confidence,'mapping_rationale':reason,
            'review_status':'test_only_project_mapping_not_human_validated','production_ready':False,
        }
        cov={**new,'masco_version':'2020','masco_code_printed':role['masco_code_printed'],'chosen_esco_isco_group':o['iscoGroup'],
            'd11_esco_code':role['esco_code'],'d11_esco_comparison_codes':p['d11_esco_comparison_codes'],
            'd11_esco_comparison_titles':display(p['d11_esco_comparison_titles'],'comparison',rid+'.d11_esco_comparison_titles'),
            'previous_d13_esco_code':p['chosen_esco_code'],'previous_d13_esco_title':esco_title(p['chosen_esco_code']),
            'previous_d13_mapping_relation':p['mapping_relation'],'original_pre2020_d13_esco_code':p.get('previous_d13_esco_code',''),
            'change_type':'changed_esco_occupation' if chosen!=p['chosen_esco_code'] else 'retained_esco_occupation',
            'mapping_method':method,'mapping_authority':'Project-derived test crosswalk; not an official MASCO-ESCO crosswalk',
            'title_match_type':alignment,'title_match_score':round(SequenceMatcher(None,nt,norm(label)).ratio(),6),
            'score_interpretation':'Fresh 2020-title lexical similarity; not a probability or proof of occupational equivalence',
            'same_four_digit_group':role['masco_unit_group_code']==o['iscoGroup'],'use_in_role_skills':True,
            'specialty_skills_complete':'Not established','source_quality_flag':p['source_quality_flag'],
            'source_current_role_id':role['source_current_role_id'],'masco2020_remap_method':role['masco2020_remap_method'],
            'profile_basis':role['profile_basis'],'masco_source_url':role['masco2020_source_url'],
            'profile_source_url':role['source_current_url'],'esco_source_url':o['conceptUri'],
            'display_case_policy':'title_case_with_protected_acronyms_and_product_spellings'}
        coverage.append(cov)
        selected=next((c for c in cr['candidates'] if c['code']==chosen),None)
        assert selected is not None,(rid,chosen,'selected candidate missing from fresh retrieval')
        evidence.append({**new,'cleaned_masco_title':cr['cleaned_title'],'masco_description':role['occupation_description'],
            'masco_tasks':role['task_summary'],'esco_description':o['description'],
            'esco_alternate_labels':display(o['altLabels'],'occupation_alternate_display',o['conceptUri']),
            'matched_esco_label':display(label,'occupation_match_label',o['conceptUri']),'matched_label_type':kind,
            'retrieval_score':selected['score'],'retrieval_score_is_probability':False,
            'query_masco_version':'2020','profile_basis':role['profile_basis'],'source_quality_flag':p['source_quality_flag'],
            'masco_source_url':role['masco2020_source_url'],'profile_source_url':role['source_current_url'],'esco_source_url':o['conceptUri']})
        review.append({**new,'priority':'high' if confidence=='low' or p['source_quality_flag'] else 'normal','reviewer':None,'review_date':None,'review_decision':None,'review_notes':None,'masco_source_url':role['masco2020_source_url'],'esco_source_url':o['conceptUri']})
        changes.append({'role_id':rid,'masco_code':role['masco_code'],'role_title':role['role_title'],
            'previous_esco_code':p['chosen_esco_code'],'previous_esco_title':esco_title(p['chosen_esco_code']),
            'chosen_esco_code':chosen,'chosen_esco_title':new['chosen_esco_title'],'esco_code_changed':chosen!=p['chosen_esco_code'],
            'previous_mapping_relation':p['mapping_relation'],'mapping_relation':relation,'mapping_method':method,'rationale':reason})
        for rank,c in enumerate(cr['candidates'],1):
            candidate_rows.append({'role_id':rid,'masco_code':role['masco_code'],'role_title':role['role_title'],'candidate_rank':rank,
                'candidate_esco_code':c['code'],'candidate_esco_title':esco_title(c['code']),'candidate_esco_uri':c['uri'],
                'retrieval_score':c['score'],'title_cosine':c['title_cosine'],'profile_cosine':c['profile_cosine'],
                'matched_esco_label':display(c['matched_label'],'candidate_match_label',c['uri']),
                'exact_normalized_label':c['exact_label'],'same_four_digit_group':role['masco_unit_group_code']==c['isco_group'],
                'selected_primary':c['code']==chosen,'query_masco_version':'2020','score_is_probability':False})
        for rejected in exact_any:
            if rejected!=chosen:
                alias_rejections.append({'role_id':rid,'masco_code':role['masco_code'],'role_title':role['role_title'],
                    'rejected_esco_code':rejected,'rejected_esco_title':esco_title(rejected),
                    'chosen_esco_code':chosen,'chosen_esco_title':new['chosen_esco_title'],'reason':reason,
                    'rejected_esco_source_url':oc[rejected]['conceptUri']})

    # Follow only official leaf-skill links for the newly selected occupations.
    relby=defaultdict(dict)
    for r in relations:
        assert r['relationType'] in {'essential','optional'}
        prev=relby[r['occupationUri']].get(r['skillUri'])
        assert prev is None or prev['relationType']==r['relationType'],'Conflicting official relation types'
        relby[r['occupationUri']][r['skillUri']]=r
    used={uri for c in coverage for uri in relby[c['chosen_esco_uri']]}
    scoped=sorted((sk[u] for u in used),key=lambda s:(s['preferredLabel'].casefold(),s['conceptUri']))
    assert len({s['conceptUri'].split('/')[-1] for s in scoped})==len(scoped)
    types={};type_rules={};definitions={};canonical={};inputs=[]
    digital='http://data.europa.eu/esco/concept-scheme/6c930acd-c104-4ece-acf7-f44fd7333036'
    for s in scoped:
        uri=s['conceptUri'];schemes=s['inScheme'].replace('\n','').split(',')
        if digital in schemes or any(x.endswith('/digcomp') for x in schemes):category,rule='digital','ESCO digital/DigComp collection membership'
        elif s['skillType']!='knowledge' and s['reuseLevel']=='transversal':category,rule='soft','Non-knowledge ESCO transversal skill; project test compatibility bucket'
        else:category,rule='technical','Default project test compatibility bucket; knowledge included; not an official ESCO skill-type equivalence'
        types[uri]=category;type_rules[uri]=rule
        definitions[uri]=(s['description'].strip() or s['definition'].strip())
        canonical[uri]=display(s['preferredLabel'],'skill',uri)
        inputs.append(canonical[uri]+'. '+definitions[uri])
    model=SentenceTransformer(MODEL,local_files_only=True,device='cpu')
    vectors=model.encode(inputs,batch_size=64,normalize_embeddings=True,show_progress_bar=True).astype(np.float32)
    assert vectors.shape==(len(scoped),384) and np.isfinite(vectors).all()
    np.save(ROOT/'05_MODEL_ARTIFACTS/D13_skill_embeddings.npy',vectors)
    taxonomy=[];skill_lineage=[];alias_pool={}
    curated={'use spreadsheets software':['Excel','MS Excel','spreadsheets'],'JavaScript':['JS','Java Script'],'SQL':['Structured Query Language']}
    for i,(s,v) in enumerate(zip(scoped,vectors)):
        uri=s['conceptUri'];sid=uri.rsplit('/',1)[-1]
        taxonomy.append({'skill_id':sid,'canonical_name':canonical[uri],'definition':definitions[uri],'skill_type':types[uri],
            'embedding':'['+','.join(f'{float(x):.8f}' for x in v)+']'})
        skill_lineage.append({'skill_id':sid,'concept_uri':uri,'preferred_label':canonical[uri],'preferred_label_raw':s['preferredLabel'],
            'skill_type':types[uri],'official_skill_type_raw':s['skillType'],'reuse_level':s['reuseLevel'],'status':s['status'],
            'modified_date':s['modifiedDate'],'definition_source_field':'description' if s['description'].strip() else 'definition',
            'skill_type_rule':type_rules[uri],'esco_in_scheme':s['inScheme'],'embedding_text':inputs[i],
            'embedding_model':MODEL,'embedding_dimensions':384,'l2_normalized':True,'source_version':'ESCO v1.2.1'})
        for source,labels in [('esco_altlabel',s['altLabels'].splitlines()),('esco_hiddenlabel',s['hiddenLabels'].splitlines()),('curated',curated.get(s['preferredLabel'],[]))]:
            for raw in labels:
                alias=match_alias(raw)
                if not alias or alias==match_alias(canonical[uri]):continue
                key=(sid,alias)
                if key not in alias_pool:alias_pool[key]={'sources':[],'raws':[],'uri':uri}
                if source not in alias_pool[key]['sources']:alias_pool[key]['sources'].append(source)
                if raw not in alias_pool[key]['raws']:alias_pool[key]['raws'].append(raw)
    aliases=[];alias_lineage=[]
    for (sid,alias),p in sorted(alias_pool.items()):
        aliases.append({'skill_id':sid,'alias':alias,'alias_source':p['sources'][0]})
        alias_lineage.append({'skill_id':sid,'alias':alias,'alias_display_title':display(p['raws'][0],'alias_display',p['uri']),
            'raw_labels_json':json.dumps(p['raws'],ensure_ascii=False),'all_alias_sources':';'.join(p['sources']),
            'normalization_rule':'NFKC + collapsed whitespace + lowercase; canonical duplicates omitted','source_url':p['uri']})
    links=[];link_lineage=[]
    for c in coverage:
        for uri,r in sorted(relby[c['chosen_esco_uri']].items()):
            base={'role_id':c['role_id'],'skill_id':uri.rsplit('/',1)[-1],'skill_name':canonical[uri],'skill_type':types[uri],
                'importance':100 if r['relationType']=='essential' else 50}
            links.append(base)
            link_lineage.append({**base,'masco_code':c['masco_code'],'masco_version':'2020','esco_code':c['chosen_esco_code'],
                'esco_occupation_title':c['chosen_esco_title'],'esco_occupation_uri':c['chosen_esco_uri'],'skill_uri':uri,
                'relation_type':r['relationType'],'official_skill_type_raw':sk[uri]['skillType'],
                'mapping_relation':c['mapping_relation'],'mapping_confidence':c['mapping_confidence'],
                'mapping_review_status':c['review_status'],'source_version':'ESCO v1.2.1','production_ready':False})
    covby={r['role_id']:r for r in coverage};updated_roles=[]
    for r in roles:
        out=convert_comparison_columns(r);c=covby[r['role_id']]
        out.update({'esco_code':c['chosen_esco_code'],'esco_title':c['chosen_esco_title'],
            'esco_crosswalk_status':'D13_MASCO2020_rebuilt_project_test_mapping','d13_previous_esco_code':r['esco_code'],
            'd13_mapping_relation':c['mapping_relation'],'d13_mapping_confidence':c['mapping_confidence']})
        updated_roles.append(out)
    preserved=[convert_comparison_columns(r) for r in read(STEM/'01_TABLES/ESCO_comparison_preservation.csv')]
    crosswalk=[convert_comparison_columns(r) for r in read(STEM/'01_TABLES/MASCO2020_role_crosswalk.csv')]
    payload={}
    def table(path,rows,columns=None):
        cols=columns or list(rows[0]);assert all(set(r)==set(cols) for r in rows),path
        payload[path]={'columns':cols,'rows':[[r[k] for k in cols] for r in rows]}
    for name,rows in {
        'D11_STEM_roles.csv':updated_roles,'D13_role_esco_coverage.csv':coverage,'D13_mapping_evidence.csv':evidence,
        'D13_mapping_candidates.csv':candidate_rows,'D13_role_esco_mapping_review.csv':review,
        'skill_taxonomy.csv':taxonomy,'skill_taxonomy_lineage.csv':skill_lineage,'skill_aliases.csv':aliases,
        'skill_aliases_lineage.csv':alias_lineage,'role_skills.csv':links,'role_skills_lineage.csv':link_lineage,
        'ESCO_comparison_preservation.csv':preserved,'MASCO2020_role_crosswalk.csv':crosswalk,
    }.items():table('01_TABLES/'+name,rows)
    table('02_QA/D13_mapping_changes.csv',changes)
    table('02_QA/D13_exact_alias_rejections.csv',alias_rejections)
    table('02_QA/D13_source_quality_issues.csv',read(STEM/'02_QA/D13_source_quality_issues.csv'))
    table('02_QA/D13_source_manifest.csv',manifest)
    table('02_QA/D13_title_case_audit.csv',sorted(audit.values(),key=lambda x:(x['label_kind'],x['reference'],x['raw_label'])))
    table('05_MODEL_ARTIFACTS/D13_skill_embedding_index.csv',[{'embedding_index':i,'skill_id':s['conceptUri'].rsplit('/',1)[-1]} for i,s in enumerate(scoped)])
    shutil.copy2(STEM/'05_MODEL_ARTIFACTS/D11_role_embeddings.npy',ROOT/'05_MODEL_ARTIFACTS/D11_role_embeddings.npy')
    shutil.copy2(STEM/'05_MODEL_ARTIFACTS/D11_role_embedding_index.csv',ROOT/'05_MODEL_ARTIFACTS/D11_role_embedding_index.csv')
    summary={'release_date':'2026-08-30','d11_masco_version':'2020','d11_role_count':len(roles),'roles_with_project_esco_mapping':len(coverage),
        'roles_with_skill_links':len({r['role_id'] for r in links}),'distinct_esco_occupations_used':len({r['chosen_esco_code'] for r in coverage}),
        'changed_primary_esco_codes':sum(c['esco_code_changed'] for c in changes),'fresh_role_retrieval_count':len(candidates),
        '2020_specific_manual_decisions':len(DECISIONS),'rejected_exact_label_candidates':len(alias_rejections),
        'mapping_relation_counts':dict(Counter(r['mapping_relation'] for r in coverage)),'mapping_confidence_counts':dict(Counter(r['mapping_confidence'] for r in coverage)),
        'scoped_leaf_skills':len(taxonomy),'skill_alias_rows':len(aliases),'role_skill_rows':len(links),
        'skill_type_counts':dict(Counter(r['skill_type'] for r in taxonomy)),'essential_role_skill_rows':sum(r['importance']==100 for r in links),
        'optional_role_skill_rows':sum(r['importance']==50 for r in links),'ESCO_comparison_source_records_preserved':len(preserved),
        'title_case_unique_audit_labels':len(audit),'title_case_labels_changed':sum(r['changed'] for r in audit.values()),
        'title_case_unit_tests_passed':tests,'raw_ESCO_sources_unchanged':True,'alias_matching_case':'lowercase',
        'embedding_model':MODEL,'embedding_dimensions':384,'l2_normalized':True,'skill_embeddings_rebuilt':True,
        'role_embeddings_unchanged':True,'remote_AI_ratings_changed':False,'schema_changed':False,'live_database_modified':False,
        'model_retrained_or_deployed':False,'human_validated_mappings':0,'official_crosswalk':False,'purpose':'test_only'}
    save(ROOT/'02_QA/D13_build_summary.json',summary)
    save(ROOT/'02_QA/build_summary.json',summary)
    save(ROOT/'02_QA/table_payloads.json',payload)
    save(ROOT/'05_MODEL_ARTIFACTS/D13_embedding_model.json',{'model':MODEL,'dimensions':384,'l2_normalized':True,
        'skill_count':len(scoped),'input_format':'Title Case canonical_name + period + ESCO description (definition fallback)',
        'min_l2_norm':float(np.linalg.norm(vectors,axis=1).min()),'max_l2_norm':float(np.linalg.norm(vectors,axis=1).max()),
        'case_policy':'Project Title Case with protected technical spellings','training_or_deployment':False})
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
