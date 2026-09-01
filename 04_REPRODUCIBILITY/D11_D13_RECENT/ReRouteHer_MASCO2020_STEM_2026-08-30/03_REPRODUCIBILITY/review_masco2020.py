"""Read-only occupation identity comparison; scores are candidates, not decisions."""
from pathlib import Path
import csv, re, json, collections, difflib, unicodedata

ROOT=Path(__file__).resolve().parents[1]
WS=ROOT.parent
CURRENT=WS/'ReRouteHer_D13_FINAL_2026-08-30'
REFERENCE=WS/'MASCO_remote_work/output/masco_2020_individual_occupations_en.csv'

def read(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def norm(s):
    s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
    return re.sub(r'[^a-z0-9]','',s)

def words(s):
    s=re.sub(r'\bgrade\b.*','',s.lower())
    return set(re.findall(r'[a-z]+',s))

def score(a,b):
    wa,wb=words(a),words(b)
    union=wa|wb
    return .55*difflib.SequenceMatcher(None,norm(a),norm(b)).ratio()+.45*len(wa&wb)/max(1,len(union))

def compare():
    current=read(CURRENT/'00_SOURCE_SNAPSHOT/D11_STEM_roles.csv')
    reference=read(REFERENCE)
    index=collections.defaultdict(list)
    for r in reference:index[norm(r['masco_occupation_title_en'])].append(r)
    result=[]
    for r in current:
        exact=index[norm(r['role_title'])]
        same=[x for x in exact if x['masco_4d_code']==r['masco_unit_group_code']]
        exact=same or exact
        pool=[x for x in reference if x['masco_4d_code']==r['masco_unit_group_code']]
        candidates=sorted(pool,key=lambda x:score(r['role_title'],x['masco_occupation_title_en']),reverse=True)[:6]
        globals_=sorted(reference,key=lambda x:score(r['role_title'],x['masco_occupation_title_en']),reverse=True)[:3] if not exact else []
        result.append({'source_role_id':r['role_id'],'source_code':r['masco_code'],'source_title':r['role_title'],
            'exact_matches':[x['masco_6d_code'].replace('-','') for x in exact],
            'candidates':[{'code':x['masco_6d_code'].replace('-',''),'title':x['masco_occupation_title_en'],'page':x['source_pdf_page'],'score':round(score(r['role_title'],x['masco_occupation_title_en']),4)} for x in candidates],
            'global_candidates':[{'code':x['masco_6d_code'].replace('-',''),'title':x['masco_occupation_title_en'],'score':round(score(r['role_title'],x['masco_occupation_title_en']),4)} for x in globals_]})
    (ROOT/'02_QA').mkdir(parents=True,exist_ok=True)
    (ROOT/'02_QA/candidate_review.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(dict(collections.Counter('unique_exact' if len(x['exact_matches'])==1 else 'ambiguous_exact' if x['exact_matches'] else 'needs_review' for x in result))))

if __name__=='__main__':compare()
