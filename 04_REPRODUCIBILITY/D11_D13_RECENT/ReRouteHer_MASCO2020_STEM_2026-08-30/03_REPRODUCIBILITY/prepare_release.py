"""Prepare auditable JSON matrices; the JS artifact builder authors final CSVs.

Taxonomy is MASCO 2020. Task/rating profiles are inherited current eMASCO D11
test data, not asserted to be verbatim 2020 task statements. ESCO assignments
remain project proxies and are never inferred from shared numeric codes.
"""
from pathlib import Path
import csv, json, re, hashlib, shutil, collections
import numpy as np
from mapping_decisions import DECISIONS
from review_masco2020 import norm

ROOT=Path(__file__).resolve().parents[1]
WS=ROOT.parent
OLD=WS/'ReRouteHer_D13_FINAL_2026-08-30'
D11=WS/'ReRouteHer_D11_STEM_2026-08-29'
PDF=WS/'MASCO_remote_work/input/masco/2020/en/MASCO_2020_English_official.pdf'
PDF_URL='https://www.dosm.gov.my/uploads/content-downloads/file_20220920110308.pdf'
GRADE_URL='https://docs.jpa.gov.my/docs/sspa/SSPA_LAMPIRAN_B.pdf'
MODEL='sentence-transformers/all-MiniLM-L6-v2'
PROFILE_BASIS='Current eMASCO D11 profile inherited for a MASCO 2020 identity; not 2020-specific task evidence; test only.'

def read(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def save(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def code(r):return r['masco_6d_code'].replace('-','')

def build():
    for folder in ['00_SOURCE_SNAPSHOT','01_TABLES','02_QA','04_DATABASE','05_MODEL_ARTIFACTS']:(ROOT/folder).mkdir(exist_ok=True)
    snapshots={
        'D11_current_STEM_roles.csv':OLD/'00_SOURCE_SNAPSHOT/D11_STEM_roles.csv',
        'MASCO_2020_individual_occupations_en.csv':WS/'MASCO_remote_work/output/masco_2020_individual_occupations_en.csv',
        'user_existing_schema.sql':OLD/'00_SOURCE_SNAPSHOT/user_existing_schema.sql'}
    for name,p in snapshots.items():shutil.copy2(p,ROOT/'00_SOURCE_SNAPSHOT'/name)
    current=read(snapshots['D11_current_STEM_roles.csv']);cur={r['role_id']:r for r in current}
    ref=read(snapshots['MASCO_2020_individual_occupations_en.csv']);rb={code(r):r for r in ref}
    review=json.loads((ROOT/'02_QA/candidate_review.json').read_text())
    cov0=read(OLD/'01_TABLES/D13_role_esco_coverage.csv');cov_by={r['role_id']:r for r in cov0}
    assert len(current)==657 and len(cur)==657 and len(rb)==6620
    decisions={};by_target=collections.defaultdict(list)
    for x in review:
        src=x['source_role_id'];d=DECISIONS.get(x['source_code'])
        if not d:
            assert len(x['exact_matches'])==1,x
            d={'targets':x['exact_matches'],'method':'exact_normalized_title','confidence':'high',
               'reason':'Exact occupation title after case, spacing and punctuation normalization. Numeric code equality was not used as proof of identity.'}
        decisions[src]=d
        for t in d['targets']:
            assert t in rb and re.fullmatch(r'\d{6}',t),t
            by_target[t].append(src)
    # One canonical profile per 2020 identity, preferring an exact-title source.
    rank={'exact_normalized_title':0,'title_variant':1,'grade_reversion':2,'duplicate_2020_title_canonical_choice':3,'reviewed_functional_equivalent':4,'combined_title_split':5}
    primary={t:min(ss,key=lambda s:(rank[decisions[s]['method']],s)) for t,ss in by_target.items()}
    targets=sorted(primary)
    payload={}
    def table(name,rows,columns=None):
        columns=columns or list(rows[0])
        payload[name]={'columns':columns,'rows':[[r.get(k,'') for k in columns] for r in rows]}
    def provenance(src,t):
        r=cur[src];rr=rb[t];d=decisions[src]
        return {'source_current_role_id':src,'source_current_masco_code':r['masco_code'],
          'source_current_role_title':r['role_title'],'source_current_url':r['source_url'],
          'masco_reference_version':'2020','masco2020_remap_method':d['method'],
          'masco2020_remap_confidence':d['confidence'],'masco2020_source_pdf_page':int(rr['source_pdf_page']),
          'masco2020_source_url':PDF_URL+'#page='+rr['source_pdf_page'],'profile_basis':PROFILE_BASIS}

    crosswalk=[];excluded=[];preserved=[]
    for src,r in cur.items():
        d=decisions[src];oldcov=cov_by[src]
        preserved.append({'source_current_role_id':src,'source_current_masco_code':r['masco_code'],
          'source_current_role_title':r['role_title'],'status':'retained' if d['targets'] else 'excluded_from_active_dataset',
          'masco2020_role_ids':';'.join('M'+t for t in d['targets']),
          'd13_esco_code':oldcov['chosen_esco_code'],'d13_esco_title':oldcov['chosen_esco_title'],
          'd11_esco_code':oldcov['d11_esco_code'],'d11_esco_comparison_codes':oldcov['d11_esco_comparison_codes'],
          'd11_esco_comparison_titles':oldcov['d11_esco_comparison_titles'],'previous_d13_esco_code':oldcov['previous_d13_esco_code'],
          'source_mapping_relation':oldcov['mapping_relation'],'source_mapping_confidence':oldcov['mapping_confidence']})
        for t in d['targets'] or ['']:
            rr=rb.get(t,{})
            row={'source_current_role_id':src,'source_current_masco_code':r['masco_code'],
              'source_current_role_title':r['role_title'],'masco2020_role_id':'M'+t if t else '',
              'masco2020_code':t,'masco2020_title':rr.get('masco_occupation_title_en',''),
              'status':'retained' if t else 'excluded','remap_method':d['method'],'remap_confidence':d['confidence'],
              'reason':d['reason'],'primary_profile_for_target':bool(t and primary[t]==src),
              'source_count_for_target':len(by_target[t]) if t else 0,
              'target_count_for_source':len(d['targets']),'source_esco_code':oldcov['chosen_esco_code'],
              'source_esco_title':oldcov['chosen_esco_title'],'source_portal_url':r['source_url'],
              'masco2020_pdf_page':int(rr['source_pdf_page']) if t else '',
              'masco2020_source_url':PDF_URL+'#page='+rr['source_pdf_page'] if t else PDF_URL,
              'grade_source_url':GRADE_URL if 'grade' in d['method'] or src in ['M221111','M238107'] else '',
              'alternative_2020_code':'311915' if src=='M311901' else '',
              'official_crosswalk':False}
            crosswalk.append(row)
            if not t:excluded.append(row.copy())
    table('01_TABLES/MASCO2020_role_crosswalk.csv',crosswalk)
    table('01_TABLES/MASCO2020_excluded_roles.csv',excluded)
    table('01_TABLES/ESCO_comparison_preservation.csv',preserved)

    # Use 2020 hierarchy headings, repairing only known text-layer word breaks.
    pages=json.loads((ROOT/'02_QA/masco2020_pdf_pages.json').read_text())
    hierarchy={}
    for p in pages[:314]:
        lines=p.splitlines()
        for i,line in enumerate(lines):
            line=' '.join(line.split())
            m=re.match(r'^(?:MAJOR|MINOR) GROUPS? (\d{1,3}) (.+)$',line,re.I) or re.match(r'^(\d{2}) ([A-Z][A-Z /,&()\-]+)$',line)
            if m:
                title=m[2]
                # Two minor headings wrap onto an all-capital continuation line.
                if i+1<len(lines) and re.fullmatch(r'[A-Z][A-Z /,&()\-]+',lines[i+1].strip()):
                    title+=' '+lines[i+1].strip()
                if len(m[1])==1 and m[1]=='6':title='SKILLED AGRICULTURAL, FORESTRY, LIVESTOCK AND FISHERY WORKERS'
                for bad,good in [('HEAL TH','HEALTH'),('CUL TURAL','CULTURAL'),('PROFFESIONAL','PROFESSIONAL'),('MALA YSIAN','MALAYSIAN'),('ROY AL','ROYAL'),('NA VY','NAVY'),('SOFTW ARE','SOFTWARE'),('SHIP ,','SHIP,'),('TRAIN/ LOCOMOTIVE','TRAIN/LOCOMOTIVE')]:title=title.replace(bad,good)
                hierarchy[m[1]]=title.title()
    legacy=read(D11/'01_TABLES/D11_STEM_D1_scope_lineage.csv')
    d1group={r['d1_masco_unit_group_code']:r for r in legacy}
    roles=[];cov=[];cov_new={};role_info={}
    for t in targets:
        src=primary[t];r=cur[src];rr=rb[t];d=decisions[src];p=provenance(src,t)
        out=r.copy();out.update(p)
        out.update({'role_id':'M'+t,'role_title':rr['masco_occupation_title_en'],'masco_code':t,
           'masco_title':rr['masco_occupation_title_en'],'masco_code_printed':rr['masco_6d_code'],
           'masco_unit_group_code':t[:4],'masco_unit_group_title':rr['masco_unit_group_title_en'],
           'source_url':p['masco2020_source_url'],'source_status':'MASCO 2020 code/title verified; current D11 profile inherited; test only',
           'task_source_level':'inherited_current_emasco_profile','rating_status':'inherited_pre_rating_not_2020_validated',
           'source_current_d11_esco_code':r['esco_code'],'source_current_esco_crosswalk_status':r['esco_crosswalk_status'],
           'esco_code':cov_by[src]['chosen_esco_code'],'esco_crosswalk_status':'D13_project_test_proxy_inherited',
           'all_source_current_role_ids':';'.join(by_target[t]),'source_profile_year':'2026 portal snapshot; enhancement edition not inferred',
           'stem_membership_basis':'Inherited current official eMASCO STEM category; not a historical 2020 STEM designation',
           'role_embedding_basis':'MASCO 2020 role title plus inherited current task_summary; recomputed with existing MiniLM; no model training'})
        for n,name in [(1,'major'),(2,'sub_major'),(3,'minor')]:
            out[f'masco_{name}_group_code']=t[:n]
            out[f'masco_{name}_group_title']=hierarchy.get(t[:n],'')
            assert out[f'masco_{name}_group_title'],(t,name)
        old_d1=d1group.get(t[:4])
        out['d1_parent_role_id']=old_d1['d1_role_id'] if old_d1 else ''
        out['d1_parent_role_title']=old_d1['d1_role_title'] if old_d1 else ''
        out['d1_expansion_relationship']='same_MASCO2020_unit_group_as_D1_seed' if old_d1 else 'additional_STEM_occupation_with_verified_MASCO2020_identity'
        roles.append(out);role_info['M'+t]=out
        c=cov_by[src].copy();c.update(p)
        c.update({'role_id':'M'+t,'role_title':out['role_title'],'masco_code':t,'masco_unit_group_code':t[:4],
           'masco_code_printed':rr['masco_6d_code'],'masco_source_url':p['masco2020_source_url'],
           'source_d13_mapping_relation':c['mapping_relation'],'source_d13_mapping_confidence':c['mapping_confidence'],
           'all_source_current_role_ids':';'.join(by_target[t]),'production_ready':'False'})
        if d['method'] in ['combined_title_split','reviewed_functional_equivalent','duplicate_2020_title_canonical_choice']:
            c['mapping_relation']='inherited_test_proxy'
            c['mapping_confidence']='low' if d['method']=='combined_title_split' else 'medium' if c['mapping_confidence']=='high' else c['mapping_confidence']
            c['mapping_rationale']='Inherited current-role ESCO assignment, not independently revalidated for this MASCO 2020 identity. '+d['reason']+' Original rationale: '+c['mapping_rationale']
        c['review_status']='test_only_project_mapping_not_human_validated'
        c['source_d13_same_four_digit_group']=c['same_four_digit_group']
        c['same_four_digit_group']=str(t[:4]==c['chosen_esco_isco_group'])
        c['title_match_evidence_basis']='Original current-role title, not the remapped 2020 title; retained for comparison only.'
        c['score_interpretation']='Inherited current-role retrieval score; not a probability or a new MASCO 2020 validation score.'
        cov.append(c);cov_new['M'+t]=c

    # A changed taxonomy label must not leave the old role embedding silently attached.
    from sentence_transformers import SentenceTransformer
    enc=SentenceTransformer(MODEL,local_files_only=True,device='cpu')
    inputs=[r['role_title']+'. '+r['task_summary'] for r in roles]
    vectors=enc.encode(inputs,batch_size=64,normalize_embeddings=True,show_progress_bar=True).astype(np.float32)
    assert vectors.shape==(len(roles),384) and np.isfinite(vectors).all()
    np.save(ROOT/'05_MODEL_ARTIFACTS/D11_role_embeddings.npy',vectors)
    for r,v in zip(roles,vectors):r['role_embedding_384']='['+','.join(f'{float(x):.8f}' for x in v)+']'
    table('01_TABLES/D11_STEM_roles.csv',roles)
    table('01_TABLES/D13_role_esco_coverage.csv',cov)
    table('05_MODEL_ARTIFACTS/D11_role_embedding_index.csv',[{'embedding_index':i,'role_id':r['role_id']} for i,r in enumerate(roles)])
    table('01_TABLES/MASCO2020_retained_roles.csv',[{'role_id':r['role_id'],'masco_code':r['masco_code'],'role_title':r['role_title'],
        'unit_group_code':r['masco_unit_group_code'],'unit_group_title':r['masco_unit_group_title'],
        'source_current_role_ids':r['all_source_current_role_ids'],'source_current_title':r['source_current_role_title'],
        'remap_method':r['masco2020_remap_method'],'remap_confidence':r['masco2020_remap_confidence'],
        'esco_code':r['esco_code'],'masco2020_source_url':r['masco2020_source_url']} for r in roles])

    primary_targets=collections.defaultdict(list)
    for t,src in primary.items():primary_targets[src].append(t)
    def rekey(rows,kind='generic'):
        result=[]
        for old in rows:
            src=old['role_id']
            for t in primary_targets[src]:
                r=old.copy();r.update(provenance(src,t));r['role_id']='M'+t
                if 'role_title' in r:r['role_title']=rb[t]['masco_occupation_title_en']
                if 'masco_code' in r:r['masco_code']=t
                if 'masco_unit_group_code' in r:r['masco_unit_group_code']=t[:4]
                if 'masco_task_id' in r:
                    r['source_current_masco_task_id']=old['masco_task_id']
                    r['masco_task_id']='MASCO2020_'+t+'_SRC_'+old['masco_task_id']
                if 'task_source_level' in r:
                    r['source_current_task_source_level']=old['task_source_level'];r['task_source_level']='inherited_current_emasco_profile'
                if 'masco_source_page_pdf' in r:r['masco_source_page_pdf']=rb[t]['source_pdf_page']
                if kind=='d13':
                    c=cov_new['M'+t]
                    r['retrieval_evidence_basis']='Original current-role title and profile; candidate scores were not recomputed for the MASCO 2020 title.'
                    if 'same_four_digit_group' in r:
                        r['source_d13_same_four_digit_group']=old['same_four_digit_group']
                        esco_group=old.get('candidate_esco_code',c['chosen_esco_code']).split('.')[0]
                        r['same_four_digit_group']=str(t[:4]==esco_group)
                    for key in ['mapping_relation','mapping_confidence','mapping_rationale','review_status','production_ready']:
                        if key in r:r['source_d13_'+key]=old[key];r[key]=c[key]
                    if 'mapping_review_status' in r:r['mapping_review_status']=c['review_status']
                    if 'masco_source_url' in r:r['masco_source_url']=provenance(src,t)['masco2020_source_url']
                    if 'cleaned_masco_title' in r:
                        r['source_d13_cleaned_masco_title']=old['cleaned_masco_title']
                        r['cleaned_masco_title']=rb[t]['masco_occupation_title_en']
                result.append(r)
        return sorted(result,key=lambda r:(r['role_id'],str(r.get('task_rank','')),r.get('skill_id','')))
    for name in ['D11_STEM_role_tasks.csv','D11_STEM_task_rating_lineage.csv','D11_STEM_role_rating_lineage.csv']:
        table('01_TABLES/'+name,rekey(read(D11/'01_TABLES'/name)))
    for r in legacy:
        r['stem_roles_in_same_unit_group']=sum(x['masco_unit_group_code']==r['d1_masco_unit_group_code'] for x in roles)
        r['d11_scope_rule']='Current eMASCO STEM membership intersected with reviewed MASCO 2020 occupation identities'
    table('01_TABLES/D11_STEM_D1_scope_lineage.csv',legacy)
    for name in ['D13_role_esco_mapping_review.csv','D13_mapping_evidence.csv','D13_mapping_candidates.csv']:
        table('01_TABLES/'+name,rekey(read(OLD/'01_TABLES'/name),'d13'))
    links=rekey(read(OLD/'01_TABLES/role_skills.csv'),'d13')
    lineage=rekey(read(OLD/'01_TABLES/role_skills_lineage.csv'),'d13')
    table('01_TABLES/role_skills.csv',links);table('01_TABLES/role_skills_lineage.csv',lineage)
    skill_ids={x['skill_id'] for x in links}
    tx=[x for x in read(OLD/'01_TABLES/skill_taxonomy.csv') if x['skill_id'] in skill_ids]
    for name in ['skill_taxonomy.csv','skill_taxonomy_lineage.csv','skill_aliases.csv']:
        table('01_TABLES/'+name,[x for x in read(OLD/'01_TABLES'/name) if x['skill_id'] in skill_ids])
    si=read(OLD/'05_MODEL_ARTIFACTS/D13_skill_embedding_index.csv')
    source_vectors=np.load(OLD/'05_MODEL_ARTIFACTS/D13_skill_embeddings.npy')
    chosen=[x for x in si if x['skill_id'] in skill_ids]
    sv=source_vectors[[int(x['embedding_index']) for x in chosen]]
    np.save(ROOT/'05_MODEL_ARTIFACTS/D13_skill_embeddings.npy',sv)
    table('05_MODEL_ARTIFACTS/D13_skill_embedding_index.csv',[{'embedding_index':i,'skill_id':x['skill_id']} for i,x in enumerate(chosen)])
    oldissues=read(OLD/'02_QA/D13_source_quality_issues.csv')
    table('02_QA/D13_source_quality_issues.csv',rekey(oldissues))
    # Record collisions against the release currently in the test database.
    conflicts=[]
    for r in roles:
        existing=cur.get(r['role_id'])
        if existing and norm(existing['role_title'])!=norm(r['role_title']):
            conflicts.append({'role_id':r['role_id'],'masco2020_title':r['role_title'],'current_database_release_title':existing['role_title'],
              'action':'Do not append/overwrite by role_id; version-aware migration or a separate database is required.'})
    table('02_QA/MASCO2020_live_database_code_conflicts.csv',conflicts)

    summary={'input_current_STEM_roles':657,'retained_current_source_roles':sum(bool(d['targets']) for d in decisions.values()),
      'excluded_current_source_roles':len(excluded),'output_unique_MASCO2020_roles':len(roles),
      'split_source_roles':sum(len(d['targets'])>1 for d in decisions.values()),
      'additional_rows_from_splits':sum(max(0,len(d['targets'])-1) for d in decisions.values()),
      'merged_duplicate_source_rows':sum(len(ss)-1 for ss in by_target.values()),
      'masco2020_reference_codes':len(rb),'roles_with_ESCo_assignment':len(cov),
      'skills':len(skill_ids),'aliases':len(payload['01_TABLES/skill_aliases.csv']['rows']),
      'role_skill_links':len(links),'role_tasks':len(payload['01_TABLES/D11_STEM_role_tasks.csv']['rows']),
      'ESCO_comparison_source_records_preserved':len(preserved),
      'current_database_release_code_title_conflicts':len(conflicts),
      'exclusion_reasons':dict(collections.Counter(x['remap_method'] for x in excluded)),
      'source_remap_methods':dict(collections.Counter(d['method'] for d in decisions.values())),
      'D13_effective_mapping_relations':dict(collections.Counter(x['mapping_relation'] for x in cov)),
      'schema_changed':False,'live_database_modified':False,'model_retrained_or_deployed':False,
      'role_embeddings_recomputed':True,'skill_embeddings_filtered_without_changes':True,
      'STEM_scope_basis':'Current official STEM category retained; no retrospective claim that 2020 separately tagged these roles as STEM.',
      'publication_warning':'Official 2020 publication reports 6630 titles; the existing audited English systematic-index extraction contains 6620 distinct codes. No missing codes are invented.',
      'purpose':'test_only','official_MASCO_version_crosswalk':False}
    save(ROOT/'02_QA/build_summary.json',summary)
    save(ROOT/'02_QA/table_payloads.json',payload)
    save(ROOT/'02_QA/selected_profiles.json',{'primary_source_by_target':primary,'source_decisions':decisions})
    save(ROOT/'05_MODEL_ARTIFACTS/embedding_metadata.json',{'model':MODEL,'dimensions':384,'l2_normalized':True,
      'role_count':len(roles),'role_embedding_input':'MASCO 2020 role title + period + inherited current D11 task_summary',
      'role_embedding_note':'Existing model inference only; no fine-tuning or deployed model update.',
      'skill_count':len(skill_ids),'skill_embedding_note':'Exact row subset of original D13 skill embeddings; not regenerated.'})
    save(ROOT/'00_SOURCE_SNAPSHOT/source_manifest.json',{
      'MASCO2020_pdf':{'url':PDF_URL,'sha256':sha(PDF),'local_source':str(PDF),'redistributed':False},
      'JPA_grade_reference':{'url':GRADE_URL,'sections':'Annex B1-B8, including pilot/medical/vocational-training grade families and assistant-planning JA7=JA38'},
      'current_D11':{'path':str(D11),'category_url':'https://emasco.mohr.gov.my/directory/category/stem','snapshot_date':'2026-08-29'},
      'prior_D13':{'path':str(OLD),'tables_sha256':{p.name:sha(p) for p in sorted((OLD/'01_TABLES').glob('*.csv'))}},
      'snapshots':{name:sha(ROOT/'00_SOURCE_SNAPSHOT'/name) for name in snapshots}})
    print(json.dumps(summary,indent=2))

if __name__=='__main__':build()
