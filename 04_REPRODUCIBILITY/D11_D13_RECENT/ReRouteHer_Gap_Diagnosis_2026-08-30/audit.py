"""Read-only analysis of the released D13 CSVs and trusted, hash-verified model."""
import csv
import importlib.util
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TABLES = ROOT / 'ReRouteHer_D13_MASCO2020_2026-08-30/01_TABLES'
def read(name):
    with (TABLES / name).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))
roles = read('D11_STEM_roles.csv')
skills = read('skill_taxonomy.csv')
links = read('role_skills.csv')
aliases = read('skill_aliases.csv')
norm = lambda s: re.sub(r'\s+', ' ', s).strip().casefold()
def dupes(rows, field, ident, normalize=False):
    groups = defaultdict(list)
    for r in rows:
        key = norm(r[field]) if normalize else r[field]
        if key:
            groups[key].append(r[ident])
    return {k:v for k,v in groups.items() if len(v)>1}
esco_groups = dupes(roles, 'esco_code', 'role_id')
by_id = {r['role_id']:r for r in roles}
by_role = defaultdict(list)
for r in links:
    by_role[r['role_id']].append(r)
skill_label_ids = defaultdict(set)
skill_id_labels = defaultdict(set)
for r in links:
    skill_label_ids[norm(r['skill_name'])].add(r['skill_id'])
    skill_id_labels[r['skill_id']].add(r['skill_name'])
alias_ids = defaultdict(set)
for r in aliases:
    alias_ids[norm(r['alias'])].add(r['skill_id'])
counts = [len(by_role[r['role_id']]) for r in roles]
village = next(r for r in roles if r['role_title']=='Village Community Center Manager')
def role_detail(r):
    rs = by_role[r['role_id']]
    return {k:r[k] for k in ('role_id','role_title','masco_code','esco_code','esco_title','d13_mapping_relation','d13_mapping_confidence','ai_exposure','flexible_role')} | {
        'skills':len(rs), 'band_counts':dict(Counter(s['skill_type'] for s in rs)),
        'band_weights':{b:sum(float(s['importance']) for s in rs if s['skill_type']==b) for b in ('technical','soft','digital')},
        'essential':sum(float(s['importance'])==100 for s in rs),
        'optional':sum(float(s['importance'])==50 for s in rs),
    }
report = {
    'roles':len(roles),'skills':len(skills),'links':len(links),
    'duplicate_role_ids':dupes(roles,'role_id','role_title'),
    'duplicate_role_titles_exact':dupes(roles,'role_title','role_id'),
    'duplicate_role_titles_normalized':dupes(roles,'role_title','role_id',True),
    'duplicate_masco_codes':dupes(roles,'masco_code','role_id'),
    'shared_esco_codes':len(esco_groups),
    'roles_sharing_esco':sum(len(v) for v in esco_groups.values()),
    'unique_esco_codes':len(set(r['esco_code'] for r in roles)),
    'duplicate_skill_ids':dupes(skills,'skill_id','canonical_name'),
    'duplicate_canonical_names':dupes(skills,'canonical_name','skill_id',True),
    'duplicate_role_skill_pairs':{str(k):v for k,v in Counter((r['role_id'],r['skill_id']) for r in links).items() if v>1},
    'same_skill_label_different_ids':{k:sorted(v) for k,v in skill_label_ids.items() if len(v)>1},
    'same_skill_id_different_labels':{k:sorted(v) for k,v in skill_id_labels.items() if len(v)>1},
    'ambiguous_alias_count':sum(len(v)>1 for v in alias_ids.values()),
    'ambiguous_alias_examples':[{ 'alias':k,'ids':sorted(v)} for k,v in alias_ids.items() if len(v)>1][:10],
    'link_counts':{'min':min(counts),'median':statistics.median(counts),'max':max(counts)},
    'no_digital_band_roles':sum(not any(s['skill_type']=='digital' for s in by_role[r['role_id']]) for r in roles),
    'village':role_detail(village),
    'same_esco_as_village':[role_detail(r) for r in roles if r['esco_code']==village['esco_code']],
    'software_roles':[role_detail(r) for r in roles if re.search('software|programmer|technical specialist|application development',r['role_title'],re.I)],
    'shared_skill_examples':Counter(r['skill_id'] for r in links).most_common(5),
    'mapping_relations':dict(Counter(r['d13_mapping_relation'] for r in roles)),
}
if '--model' in sys.argv:
    source=ROOT/'ReRouteHer_Gap_Diagnosis_2026-08-30/source/backend/app/services/occupation_matcher.py'
    spec=importlib.util.spec_from_file_location('diagnostic_matcher', source)
    mod=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=mod
    spec.loader.exec_module(mod)
    matcher=mod.EscoTfidfMatcher.load(str(ROOT/'rerouteher-system/ml/tfidf_logreg.joblib'))
    report['model_catalog_size']=len(matcher.catalog)
    report['model_masco_lengths']=dict(Counter(len(str(r.get('masco_candidate_code'))) for r in matcher.catalog if r.get('masco_candidate_code')))
    report['model_predictions']={}
    for title in ['Software Developer','ICT Operations Manager','IT Manager','Data Analyst','Project Manager','Customer Service Representative','']:
        preds=matcher.predict(title,[],top_k=5)
        report['model_predictions'][title]=[
            vars(p) | {'all_matching_masco_roles':[r['role_title'] for r in roles if r['esco_code']==p.esco_code]}
            for p in preds]
print(json.dumps(report,indent=2))
