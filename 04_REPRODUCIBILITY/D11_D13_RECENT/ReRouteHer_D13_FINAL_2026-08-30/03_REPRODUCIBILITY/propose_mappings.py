"""Retrieve ESCO candidates for D11; scores are retrieval scores, not probabilities."""
from pathlib import Path
import csv, json, re, unicodedata
from collections import defaultdict
from difflib import SequenceMatcher
import numpy as np
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT.parent / 'ReRouteHer_D13_ESCO_LeafSkills_D11_2026-08-29'
D11 = ROOT.parent / 'ReRouteHer_D11_STEM_2026-08-29/01_TABLES/D11_STEM_roles.csv'
SRC = OLD / '00_SOURCE_SNAPSHOT/ESCO_v1.2.1_classification_en_csv'

def read(path):
    with path.open(encoding='utf-8-sig', newline='') as f: return list(csv.DictReader(f))

def norm(s):
    s = unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
    return ' '.join(re.findall(r'[a-z0-9]+',s))

def clean_title(s):
    s = re.sub(r'\s+Grade\s+.*$', '', s, flags=re.I)
    s = re.sub(r'^Competent Person\s*\(CP\)\s*-\s*', '', s, flags=re.I)
    s = s.replace('Scada','SCADA')
    return s.strip()

roles = read(D11)
coverage = {r['role_id']: r for r in read(OLD/'01_TABLES/D13_role_esco_coverage.csv')}
byuri={}
for row in read(SRC/'occupations_en.csv'):
    if row['conceptUri'] not in byuri or row['modifiedDate'] > byuri[row['conceptUri']]['modifiedDate']:
        byuri[row['conceptUri']]=row
occ=sorted(byuri.values(), key=lambda r:r['code'])
names=[o['preferredLabel'] for o in occ]
descs=[o['preferredLabel']+'. '+o['description'] for o in occ]
role_names=[clean_title(r['role_title']) for r in roles]
role_descs=[clean_title(r['role_title'])+'. '+r['occupation_description']+' '+r['task_summary'] for r in roles]
model=SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', local_files_only=True, device='cpu')
def emb(texts): return model.encode(texts, batch_size=64, normalize_embeddings=True, show_progress_bar=True)
ne=emb(names); de=emb(descs); rn=emb(role_names); rd=emb(role_descs)
tn=rn@ne.T; td=rd@de.T
aliases=[]; label_index=defaultdict(set)
for i,o in enumerate(occ):
    labs=[(o['preferredLabel'],'preferred')]+[(a,'alternate') for a in o['altLabels'].splitlines() if a]
    aliases.append(labs)
    for lab,typ in labs: label_index[norm(lab)].add(i)

out=[]
for i,r in enumerate(roles):
    title=role_names[i]; n=norm(title)
    candidates=set(np.argsort(tn[i])[-30:])|set(np.argsort(td[i])[-30:])|label_index[n]
    old_code=coverage[r['role_id']]['chosen_esco_code']
    candidates.update(j for j,o in enumerate(occ) if o['code']==old_code)
    scored=[]
    for j in candidates:
        o=occ[j]
        matched,typ=max(aliases[j], key=lambda x:SequenceMatcher(None,n,norm(x[0])).ratio())
        fuzzy=SequenceMatcher(None,n,norm(matched)).ratio()
        exact=norm(matched)==n
        same=r['masco_unit_group_code']==o['iscoGroup']
        score=.50*float(tn[i,j])+.35*float(td[i,j])+.15*fuzzy+.015*same
        if exact: score=max(score,.92 + .02*same)
        scored.append({'code':o['code'],'title':o['preferredLabel'],'uri':o['conceptUri'],
            'isco_group':o['iscoGroup'],'description':o['description'],'score':round(score,6),
            'title_cosine':round(float(tn[i,j]),6),'profile_cosine':round(float(td[i,j]),6),
            'matched_label':matched,'label_type':typ,'exact_cleaned_label':exact,'same_group':same})
    scored.sort(key=lambda x:(-x['score'],x['code']))
    out.append({'index':i,'role_id':r['role_id'],'masco_code':r['masco_code'],'role_title':r['role_title'],
        'cleaned_title':title,'description':r['occupation_description'],'tasks':r['task_summary'],
        'source_url':r['source_url'],'old_esco_code':old_code,'old_status':coverage[r['role_id']]['mapping_status'],
        'old_title_alignment':coverage[r['role_id']]['title_match_type'],'candidates':scored[:8]})
(ROOT/'02_QA').mkdir(parents=True,exist_ok=True)
(ROOT/'02_QA/candidate_review.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
(ROOT/'02_QA/esco_occupation_index.json').write_text(json.dumps(occ,ensure_ascii=False)+'\n')
np.savez_compressed(ROOT/'02_QA/retrieval_vectors.npz',occupation_names=ne,occupation_profiles=de,role_names=rn,role_profiles=rd)
print(json.dumps({'roles':len(out),'occupations':len(occ),'top_exact_cleaned':sum(x['candidates'][0]['exact_cleaned_label'] for x in out)}))
