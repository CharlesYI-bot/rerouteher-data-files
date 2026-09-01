"""Independent source-to-database content checks, without changing any data."""
from pathlib import Path
import csv, hashlib, json

ROOT=Path(__file__).resolve().parent
NEW=ROOT.parent/'ReRouteHer_D13_MASCO2020_2026-08-30'
PREFIX='d13_masco2020_rebuilt_20260830'

def read(name):
    with (NEW/'01_TABLES'/name).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def expected(rows,fields,sort_fields):
    ordered=sorted(rows,key=lambda r:tuple(r[k] for k in sort_fields))
    assert all('\x1f' not in r[k] for r in rows for k in fields)
    return hashlib.md5('\n'.join('\x1f'.join(r[k] for k in fields) for r in ordered).encode()).hexdigest()

def main():
    tests=[]
    def add(name,file,fields,sort,query_fields,sql_from,sql_order):
        rows=read(file);h=expected(rows,fields,sort)
        joined=" || chr(31) || ".join(query_fields)
        query=f"SELECT '{name}' AS check_name, count(*)={len(rows)} AS count_ok, md5(string_agg({joined},E'\\n' ORDER BY {sql_order}))='{h}' AS content_ok {sql_from}"
        tests.append({'name':name,'expected_rows':len(rows),'expected_md5':h,'query':query})
    add('MASCO role identities and ESCO codes','D11_STEM_roles.csv',
        ['role_id','masco_code','role_title','esco_code'],['role_id'],
        ['r.role_id','r.masco_code','r.role_title','r.esco_code'],
        f"FROM rerouteher.roles r JOIN rerouteher.dataset_metadata m ON m.metadata_key='{PREFIX}.mapping.'||r.role_id",'r.role_id COLLATE "C"')
    add('ESCO display titles','D13_role_esco_coverage.csv',
        ['role_id','chosen_esco_code','chosen_esco_title'],['role_id'],
        ["(m.metadata_value->>'role_id')","(m.metadata_value->>'chosen_esco_code')","(m.metadata_value->>'chosen_esco_title')"],
        f"FROM rerouteher.dataset_metadata m WHERE starts_with(m.metadata_key,'{PREFIX}.mapping.')",'(m.metadata_value->>\'role_id\') COLLATE "C"')
    add('Title Case canonical skills and definitions','skill_taxonomy.csv',
        ['skill_id','canonical_name','definition','skill_type'],['skill_id'],
        ['s.skill_id','s.canonical_name',"coalesce(s.definition,'')",'s.skill_type'],
        f"FROM rerouteher.skill_taxonomy s JOIN rerouteher.dataset_metadata m ON m.metadata_key='{PREFIX}.skill_type.'||s.skill_id",'s.skill_id COLLATE "C"')
    add('Lowercase aliases with provenance','skill_aliases.csv',
        ['skill_id','alias','alias_source'],['skill_id','alias'],
        ['s.skill_id','s.alias','s.alias_source'],
        f"FROM rerouteher.skill_aliases s JOIN rerouteher.dataset_metadata m ON m.metadata_key='{PREFIX}.skill_type.'||s.skill_id",'s.skill_id COLLATE "C",s.alias COLLATE "C"')
    add('Role-skill labels types and weights','role_skills.csv',
        ['role_id','skill_id','skill_name','skill_type','importance'],['role_id','skill_id'],
        ['s.role_id','s.skill_id','s.skill_name','s.skill_type','s.importance::integer::text'],
        f"FROM rerouteher.role_skills s JOIN rerouteher.dataset_metadata m ON m.metadata_key='{PREFIX}.mapping.'||s.role_id",'s.role_id COLLATE "C",s.skill_id COLLATE "C"')
    add('Preserved original ESCO comparisons','ESCO_comparison_preservation.csv',
        ['source_current_role_id','d13_esco_code','d13_esco_title','d11_esco_comparison_codes','d11_esco_comparison_titles'],['source_current_role_id'],
        [f"coalesce(m.metadata_value->>'{k}','')" for k in ['source_current_role_id','d13_esco_code','d13_esco_title','d11_esco_comparison_codes','d11_esco_comparison_titles']],
        f"FROM rerouteher.dataset_metadata m WHERE starts_with(m.metadata_key,'{PREFIX}.source_esco.')",'(m.metadata_value->>\'source_current_role_id\') COLLATE "C"')
    sql='BEGIN READ ONLY;\n'+'\nUNION ALL\n'.join(t['query'] for t in tests)+';\nCOMMIT;\n'
    (ROOT/'verify_exact_source_content.sql').write_text(sql)
    (ROOT/'expected_source_checks.json').write_text(json.dumps(tests,indent=2)+'\n')
    print(json.dumps([{k:v for k,v in t.items() if k!='query'} for t in tests],indent=2))

if __name__=='__main__':main()
