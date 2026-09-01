"""Fresh 2020-title retrieval; reuse only verified unchanged ESCO-side vectors."""
from collections import defaultdict
from difflib import SequenceMatcher
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from common import ROOT,STEM,PRIOR,ESCO,MODEL,read,save,sha,latest,norm,clean_title

def main():
    roles=read(STEM/'01_TABLES/D11_STEM_roles.csv')
    old={r['role_id']:r for r in read(STEM/'01_TABLES/D13_role_esco_coverage.csv')}
    occ=sorted(latest(read(ESCO/'occupations_en.csv')),key=lambda r:r['code'])
    archived=json.loads((PRIOR/'02_QA/esco_occupation_index.json').read_text())
    assert occ==archived,'ESCO vector cache identity/order mismatch'
    cache=np.load(PRIOR/'02_QA/retrieval_vectors.npz')
    ne,de=cache['occupation_names'],cache['occupation_profiles']
    assert ne.shape==de.shape==(len(occ),384)
    model=SentenceTransformer(MODEL,local_files_only=True,device='cpu')
    titles=[clean_title(r['role_title']) for r in roles]
    profiles=[t+'. '+r['occupation_description']+' '+r['task_summary'] for t,r in zip(titles,roles)]
    rn=model.encode(titles,batch_size=64,normalize_embeddings=True,show_progress_bar=True)
    rp=model.encode(profiles,batch_size=64,normalize_embeddings=True,show_progress_bar=True)
    tn,tp=rn@ne.T,rp@de.T
    index=defaultdict(set);prefs=defaultdict(set);labels=[];bycode={o['code']:i for i,o in enumerate(occ)}
    for i,o in enumerate(occ):
        labs=[(o['preferredLabel'],'preferred')]+[(x,'alternate') for x in o['altLabels'].splitlines() if x.strip()]
        labels.append(labs);prefs[norm(o['preferredLabel'])].add(i)
        for label,kind in labs:index[norm(label)].add(i)
    out=[]
    for i,r in enumerate(roles):
        nt=norm(titles[i]);prev=old[r['role_id']]['chosen_esco_code']
        candidates=set(np.argsort(tn[i])[-30:])|set(np.argsort(tp[i])[-20:])|index[nt]|{bycode[prev]}
        scored=[]
        for j in candidates:
            o=occ[j]
            label,kind=max(labels[j],key=lambda x:SequenceMatcher(None,nt,norm(x[0])).ratio())
            lexical=SequenceMatcher(None,nt,norm(label)).ratio()
            score=.65*float(tn[i,j])+.20*float(tp[i,j])+.15*lexical
            if nt==norm(o['preferredLabel']):score=max(score,.995)
            elif nt in {norm(x) for x in o['altLabels'].splitlines()}:score=max(score,.985)
            scored.append({'code':o['code'],'title':o['preferredLabel'],'uri':o['conceptUri'],'description':o['description'],
                'score':round(score,6),'title_cosine':round(float(tn[i,j]),6),'profile_cosine':round(float(tp[i,j]),6),
                'matched_label':label,'label_type':kind,'exact_label':norm(label)==nt,'isco_group':o['iscoGroup']})
        scored.sort(key=lambda c:(-c['score'],c['code']))
        selected=scored[:10]
        if prev not in {c['code'] for c in selected}:selected.append(next(c for c in scored if c['code']==prev))
        out.append({'role_id':r['role_id'],'masco_code':r['masco_code'],'role_title':r['role_title'],'cleaned_title':titles[i],
            'remap_method':r['masco2020_remap_method'],'source_current_role_id':r['source_current_role_id'],
            'prior_esco_code':prev,'prior_relation':old[r['role_id']]['mapping_relation'],
            'original_d13_relation':old[r['role_id']]['source_d13_mapping_relation'],
            'prior_rationale':old[r['role_id']]['mapping_rationale'],
            'exact_preferred_codes':[occ[j]['code'] for j in sorted(prefs[nt])],
            'exact_label_codes':[occ[j]['code'] for j in sorted(index[nt])],
            'candidates':selected})
    save(ROOT/'02_QA/candidate_review.json',out)
    save(ROOT/'02_QA/retrieval_metadata.json',{'role_count':len(roles),'esco_occupation_count':len(occ),
        'role_input':'Cleaned MASCO 2020 title; fresh embeddings for titles and inherited profiles',
        'score_formula':'0.65 title cosine + 0.20 profile cosine + 0.15 lexical similarity; exact-label rank boosts',
        'masco_isco_numeric_prefix_used_in_ranking':False,'score_is_probability':False,
        'cached_ESCO_vectors_verified_against_full_occupation_records':True,
        'ESCO_source_sha256':sha(ESCO/'occupations_en.csv'),'D11_2020_source_sha256':sha(STEM/'01_TABLES/D11_STEM_roles.csv')})
    np.savez_compressed(ROOT/'02_QA/retrieval_vectors.npz',occupation_names=ne,occupation_profiles=de,role_names=rn,role_profiles=rp)
    print(json.dumps({'roles':len(out),'unique_exact_preferred':sum(len(x['exact_preferred_codes'])==1 for x in out),
        'unique_exact_any_label':sum(len(x['exact_label_codes'])==1 for x in out),
        'top_candidate_differs_from_inherited':sum(x['candidates'][0]['code']!=x['prior_esco_code'] for x in out),
        'functional_or_split_targets':sum(x['remap_method'] in ['combined_title_split','reviewed_functional_equivalent','duplicate_2020_title_canonical_choice'] for x in out)}))

if __name__=='__main__':main()
