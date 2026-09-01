from pathlib import Path
import csv, hashlib, json, re, unicodedata

ROOT=Path(__file__).resolve().parents[1]
STEM=ROOT.parent/'ReRouteHer_MASCO2020_STEM_2026-08-30'
PRIOR=ROOT.parent/'ReRouteHer_D13_FINAL_2026-08-30'
ESCO=PRIOR/'00_SOURCE_SNAPSHOT/ESCO_v1.2.1_classification_en_csv'
MODEL='sentence-transformers/all-MiniLM-L6-v2'

def read(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def save(p,value):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def latest(rows):
    by={}
    for r in rows:
        if r['conceptUri'] not in by or r['modifiedDate']>by[r['conceptUri']]['modifiedDate']:by[r['conceptUri']]=r
    return list(by.values())
def norm(s):
    return ' '.join(re.findall(r'[a-z0-9]+',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()))
def clean_title(s):
    s=re.sub(r'\s+Grade\s+.*$','',s,flags=re.I)
    s=re.sub(r'^Competent Person\s*\(CP\)\s*-\s*','',s,flags=re.I)
    return ' '.join(s.split()).strip()

