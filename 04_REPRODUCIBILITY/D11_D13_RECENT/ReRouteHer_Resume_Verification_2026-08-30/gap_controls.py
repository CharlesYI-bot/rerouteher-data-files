"""Four stateless scoring controls; no additional resumes or personal data."""
from analyze_results import fixtures
from verify_resumes import OUT, post, save

roles, taxonomy, links, _ = fixtures()
cases = []
for title in ('Village Community Center Manager', 'Teacher, Vocational', 'Technical Specialist (.Net)'):
    cases.append({'control':'empty_profile','target_role':title,'skills':[]})
title='Technical Specialist (.Net)'
cases.append({'control':'all_24_active_core_ids','target_role':title,
              'skills':[{'skill':s['skill_name'],'skill_id':s['skill_id'],'source':'experience'}
                        for s in links[roles[title]['role_id']]]})
results=[]
for c in cases:
    http,result=post('/api/gap/compute',payload={k:c[k] for k in ('target_role','skills')})
    results.append({'control':c['control'],'target_role':c['target_role'],
                    'input_skill_count':len(c['skills']),'http':http,'result':result})
save(OUT/'gap_controls.json',results)
for r in results:
    print(r['control'],r['target_role'],r['http']['status'],r['result']['readiness'])
