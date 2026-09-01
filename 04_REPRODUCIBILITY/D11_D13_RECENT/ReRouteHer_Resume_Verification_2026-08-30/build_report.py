"""Build the human-readable report from frozen test evidence."""
import json
from pathlib import Path

P=Path(__file__).resolve().parent
load=lambda name:json.loads((P/name).read_text())
raw=load('live_results.json'); audit=load('audit_results.json'); manifest=load('sample_manifest.json')
expected={c['case_id']:c for c in load('review_expectations.json')['cases']}
review=load('manual_review.json'); s=audit['summary']
assert len(raw['cases'])==25 and len(audit['gaps'])==75
assert not s['score_mismatches'] and not s['matched_skill_mismatches']

def link(name,label=None):
    return f'[{label or name}](<{P/name}>)'

text=f'''# ReRouteHer: 25-resume application verification

30 August 2026 | https://rerouteher.curl.my/

## Verdict

**Functional requests pass; role relevance and readiness reliability fail.** Do not use these scores as validated assessments of a person's capability or employability.

The most urgent regression is that low-confidence roles whose skill requirements were withheld by the previous data-only cleanup remain selectable. The unchanged scorer considers an empty requirement set fully covered and returns **100%**. The browser then says both “Ready today” and “None of your skills matched.” The earlier database integrity checks did not catch this end-to-end failure.

No application/backend code, model, dataset, database structure or database rows were changed in this verification. This was testing only, not training or a fix.

## What was tested

- 25 distinct original PDFs, deterministically sampled from 2,484 PDFs across 24 source folders; the sample covers {len(manifest['quotas'])} folders, with extra IT, engineering and teaching cases.
- All 25: original PDF -> live `/api/cv/parse` -> **unedited parsed CV** -> `/api/snapshot/generate` -> `/api/gap/compute` for all three suggested roles.
- 125 primary requests: 25 parses, 25 snapshots and 75 gap calculations. All returned HTTP 200. Those 75 recommendations cover 57 distinct catalogue roles.
- Two complete browser journeys, T01 and T17, plus switching roles on the gap page. The other 23 resumes were tested through the same live API, not manually clicked through the UI.
- Four additional stateless controls using empty skills or valid reference skill IDs, with no extra personal data.
- API isolation settings: synthetic two-year break, no activities. Browser settings: displayed “Less than a year,” with synthetic “Managing schedules” activity because the form requires one. These are test inputs, not facts about the resume owners. Both browser snapshots added Scheduling and Coordination; the tested role recommendations and scores matched the API cases.
- Expected occupational families were recorded before live results. Folder labels are **not** ground truth: the agriculture-folder sample is an adult-education teacher, and the automobile-folder sample is a secretary.

Primary API run: {raw['started_utc']} to {raw['last_updated_utc']} (UTC). Median observed parsing latency: **{s['median_parse_seconds']:.1f}s**; maximum **{s['max_parse_seconds']:.1f}s**. Median snapshot: {s['median_snapshot_seconds']:.2f}s; median gap calculation: {s['median_gap_seconds']:.2f}s. This is a small sequential functional test, not a load test or SLA measurement.

## Measured results

| Check | Result |
|---|---:|
| PDF parsing returned HTTP 200 | 25/25 |
| Snapshot returned HTTP 200 and three recommendations | 25/25 |
| Gap requests returned HTTP 200 | 75/75 |
| Readiness 100%, with zero active requirements and zero matched skills | **25/75** |
| Resumes with at least one such false 100% recommendation | **16/25** |
| First/default recommendation affected by false 100% | **9/25** |
| Scores equal to 0% | **19/75** |
| Scores from 0% through 3%, inclusive | **22/75** |
| Previous-occupation confidence below 0.65 | 22/25 |
| Severe experience/title extraction failures identified manually | 6/25 |
| Returned extracted skill occurrences | 836 |
| Missing or unknown extracted skill IDs | 0 |
| Duplicate skill IDs / duplicate normalized skill labels within a snapshot | 0 / 0 |
| Duplicate normalized recommended titles within a snapshot | 0 |
| Outdated canonical skill labels versus applied reference data | 2 |
| Recommendations joining to six-digit MASCO entries in the catalogue | 69/75 |
| Recommendations joining to retained four-digit legacy entries | 6/75 |

All 75 scores and matched-skill sets reproduce exactly from the applied data release and the documented scoring formula. That establishes implementation/fixture consistency, **not assessment validity**. Zero is not automatically a bug for an unsuitable target; the particular zero-score failures below show why it cannot be interpreted as zero capability.

## 1. Empty requirements produce false 100% readiness — critical

All 25 false-100% recommendations correspond to **Low-confidence, unapproved** mappings with zero active requirements (19 distinct roles). The previous cleanup appropriately withheld unapproved skill links, but did not remove those roles from every recommendation/scoring path. The backend does not consult mapping approval before scoring and its empty-band coverage defaults to 1.0.

- T01: IT/BI management -> Operation Research Analyst, **100%**, no matches or gaps.
- T17: adult-education teacher -> **Village Community Center Manager**, **100%**, no matches or gaps. This reproduces the originally reported unwanted role in the browser.
- T20: digital artist -> Technical Artist, Graphics Creator and Graphics Programmer; all three score **100%** from missing requirements.

This is an integration failure exposed by the data-only update, not evidence the people are ready for those occupations. Restoring every optional skill as a universal requirement would recreate the earlier overlarge-denominator problem and is not an appropriate remedy.

Browser evidence: {link('ui_false_100_readiness.png','false 100% screen')}; {link('ui_village_manager.png','Village manager screen')}.

## 2. An empty single band also creates free readiness

Even when a role has requirements, an absent digital band receives full digital credit. Three sampled recommendations scored positively with **zero** matched skills:

| Case | Role | Active requirements | Score with zero matches |
|---|---|---:|---:|
| T07 | Plywood Inspection Supervisor | 16 | 60% |
| T18 | Coroner | 9 | 40% |
| T22 | Welding Manager | 22 | 20% |

An additional empty-input control for Teacher, Vocational returned **20%**. An empty-input Village control returned **100%**. Missing evidence/requirements must not be represented as demonstrated coverage.

## 3. Role matching still accepts unrelated or unsupported occupations

Clear mismatch examples, based on the resume work content rather than folder labels:

| Case | Resume profile | Returned previous occupation |
|---|---|---|
| T03 | Operations research analyst | Online Marketing Specialist |
| T05 | ASP.NET web developer | Management Information Systems (MIS) Analyst |
| T08 | Facilities/building engineering manager | Railway Station Master |
| T10 | Substitute teacher | Test Analyst (Information Technology), confidence **0.018** |
| T14 | Consumer-business CEO | Chief data officer |
| T19 | Industrial/aircraft maintenance mechanic | Track Network Technician |
| T22 | Finance coordinator | Port Captain |
| T24 | Retail sales associate | Technical Sales Engineer |

These are qualitative findings, not an accuracy benchmark with certified MASCO labels. Some adjacent recommendations may support a career transition but must not be presented as the person's previous occupation without evidence. Seniority, qualifications and Malaysian public-service grades are not established just because the broad family is similar.

The known resolver still maps shared ESCO comparison codes to the first matching MASCO row, uses a four-digit prefix fallback, and fills recommendations without a suitability floor. These mechanisms are consistent with the observed results, but an individual request's exact internal resolution branch was not captured from server logs. Shared ESCO comparison codes must remain valid many-to-one comparisons—not be deleted to force uniqueness.

Six returned suggestions correspond to retained legacy codes 2431, 2311, 4121 or 4311. The response itself returns role **titles only**, not role IDs, MASCO codes or ESCO codes; the six-digit counts above are catalogue joins, not codes asserted by the API. The application therefore still does not provide a verifiable six-digit identity end-to-end.

## 4. PDF extraction and skill recognition are not reliable enough

The PDF skill's local text/visual checks confirmed readable source content. HTTP 200 therefore does not mean correct extraction:

- T04, T13, T15 and T23: all parsed job-title fields consist of company/location placeholders, despite actual job titles in the PDFs.
- T05: university/degree text was returned as work experiences, losing the ASP.NET developer title.
- T10: zero experiences were returned despite a substitute-teacher work-history section.

The software-engineering team-lead PDF (T06) describes software development and lists C#, VB.NET, web technologies and Agile/Scrum. Nevertheless the result includes **Turf Management**, **Conduct Research on Flora**, Lisp, MATLAB and Swift. The latter terms are not in the PDF; turf/flora are substantively unrelated. The parser's approximate string matching returns dictionary labels as if they were source evidence, so a fuzzy match can become an apparently exact skill in the snapshot. Separately, T01's ordinary word “did” was interpreted as Direct Inward Dialing. These are concrete false-positive examples, not a comprehensive precision/recall audit.

## 5. The 0% software example is a data-to-extraction mismatch

T06 -> Technical Specialist (.Net) is a plausible software-family match, yet scores **0%**:

- 40 extracted skills, all with known IDs.
- Zero overlap with this role's **24 active core skill IDs**.
- Thirteen extracted IDs appear in its held optional inventory; some are real technologies from the resume and some are extraction false positives.
- The core includes broader competencies such as Computer Programming, Debug Software and Define Technical Requirements. The extractor did not produce those exact IDs from this resume's descriptions.
- A control supplying all 24 active core IDs returned **100%**; an empty-skill control returned **0%**. The formula is executing its contract, but the extraction and role-requirement design do not provide a credible capability assessment.

Do not fix this by awarding arbitrary fuzzy credit or making all optional specialisms mandatory again. Core requirements and extraction evidence need role-specific review together.

## 6. Display counts and cache freshness still need attention

T01's Supervisor, Management Information Systems page says **“You meet 1 of 4 requirements”** at 1.4%. The role actually has **32** active requirements. The UI adds one match to only the three returned focus gaps. Across the sample, this formula understates the total for **all 50 non-empty requirement sets**. The 25 empty sets are a different failure and should display “not assessed.” Evidence: {link('ui_requirement_count.png','incorrect requirement count screen')}.

Two exact-pass labels are stale relative to the applied canonical taxonomy:

- T05: `DIGCOMP_3_4` returned “Programming,” not “Programming (DigComp Competence).”
- T10: `ONET_2_A_1_e` returned “Mathematics,” not “Mathematics (O*NET Skill).”

Other semantic results use updated labels. This is consistent with the cached alias/canonical lookup coexisting with fresh database queries. Deployment process/cache state was not inspected or restarted. The successful within-snapshot duplicate checks do not establish that caches are fresh or meanings are correct.

## Correction priorities — recommendations only, not applied

1. Exclude unapproved/unscorable roles from **all** recommendation routes and return an explicit “not assessed” outcome for zero requirements. `flexible_role=false` alone would not cover the classifier-first path. Use existing metadata/relationships; no schema redesign is needed just to add the guard.
2. Remove free credit for absent bands and review the scoring interpretation. Keep core/conditional distinctions; do not restore the old universal optional-skill denominator.
3. Fix experience segmentation, title cleanup and approximate skill evidence. Add these PDFs as held-out regression tests, not training inputs.
4. Resolve a stable six-digit MASCO identity with contextual ranking, a rejection/uncertainty path and explicit ESCO comparison status. Do not force three unsuitable occupations.
5. Review representative role core sets together with extraction outputs; refresh/version caches and browser snapshots when data changes.
6. Return/display the true requirement total, separately from the top-three focus list. Review request/response body logging for personal-data retention.

The user requested verification and previously limited backend changes, so none of these fixes was implemented. These findings show why dataset deduplication alone cannot make the current app reliable.

## Every sampled resume — primary results

Scores below are the **observed application outputs**, not endorsed readiness estimates. All three role outputs and skill IDs are available in the machine-readable evidence.

| Case | Resume profile | Top returned role | Score | Active requirements |
|---|---|---|---:|---:|
'''
by_case={g['case_id']:g for g in audit['gaps'] if g['rank']==1}
for c in raw['cases']:
    key=c['case_id']; g=by_case[key]
    text+=f"| {key} | {expected[key]['profile']} | {g['role']} | {g['readiness']:g}% | {g['requirements']} |\n"
text+='\n## Case review notes\n\n'
for key,note in review['notes'].items():
    text+=f'- **{key}:** {note}\n'
text+=f'''
## Evidence, reproducibility and limitations

- {link('sample_manifest.json','Sample manifest')}: original relative paths, SHA-256 hashes, deterministic seed, category quotas, page/text counts. All 25 selected PDF hashes are distinct.
- {link('live_results.json','Filtered live results')}: primary HTTP statuses/timings, parsed title fields, skill IDs, recommendations and gap outputs. Full resume text, experience descriptions and contact details were not copied into this evidence file.
- {link('audit_results.json','Reconciliation audit')}: all 75 role/skill/score checks and catalogue joins; zero formula or matched-skill discrepancies.
- {link('gap_controls.json','Four scoring controls')}; {link('ui_observations.json','Browser observations')}; {link('manual_review.json','Manual review notes')}.
- Reference data: applied `ReRouteHer_Data_Quality_Fix_2026-08-30` release, with the seven retained legacy role fixtures. This was not a fresh full-database duplicate audit. No database connection or mutation was made during verification.
- Relevant inspected source: [scoring](https://github.com/ryus0006/rerouteher-system/blob/23ed6b88a54be269449715656cc51d21c8e8af3b/app/services/gap.py), [PDF extraction](https://github.com/ryus0006/rerouteher-system/blob/23ed6b88a54be269449715656cc51d21c8e8af3b/app/services/cv_extractor.py), [role lookup](https://github.com/ryus0006/rerouteher-system/blob/23ed6b88a54be269449715656cc51d21c8e8af3b/app/repositories/roles.py), [snapshot](https://github.com/ryus0006/rerouteher-system/blob/23ed6b88a54be269449715656cc51d21c8e8af3b/app/services/snapshot.py), [gap display](https://github.com/ryus0006/rerouteher-ui/blob/4e2603812196112cd1807f87388d53e4c5f9709a/src/routes/Gap.jsx), [body logging](https://github.com/ryus0006/rerouteher-system/blob/main/app/core/logging.py). Exact deployed commit was not independently inspected; live responses/browser states are the behavioral evidence.
- Small, deliberately stratified sample; not population accuracy, Malaysia-specific occupational validation, fairness testing, OCR testing, a security audit, or production acceptance. No certified six-digit ground-truth labels or human readiness scores were supplied.
- Original PDFs were not edited or copied into the deliverable. User explicitly approved transmitting them after being informed that parsed content may be retained in application logs. No training occurred, no accounts were created and no server logs were deleted. Temporary browser test CV state was removed after evidence capture; this does not delete server logs.
'''
(P/'VERIFICATION_REPORT.md').write_text(text)
print(f'Created report: {len(text)} characters; 25 case rows; 75 scoring records.')
