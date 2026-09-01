# ReRouteHer: 25-resume application verification

30 August 2026 | https://rerouteher.curl.my/

## Verdict

**Functional requests pass; role relevance and readiness reliability fail.** Do not use these scores as validated assessments of a person's capability or employability.

The most urgent regression is that low-confidence roles whose skill requirements were withheld by the previous data-only cleanup remain selectable. The unchanged scorer considers an empty requirement set fully covered and returns **100%**. The browser then says both “Ready today” and “None of your skills matched.” The earlier database integrity checks did not catch this end-to-end failure.

No application/backend code, model, dataset, database structure or database rows were changed in this verification. This was testing only, not training or a fix.

## What was tested

- 25 distinct original PDFs, deterministically sampled from 2,484 PDFs across 24 source folders; the sample covers 14 folders, with extra IT, engineering and teaching cases.
- All 25: original PDF -> live `/api/cv/parse` -> **unedited parsed CV** -> `/api/snapshot/generate` -> `/api/gap/compute` for all three suggested roles.
- 125 primary requests: 25 parses, 25 snapshots and 75 gap calculations. All returned HTTP 200. Those 75 recommendations cover 57 distinct catalogue roles.
- Two complete browser journeys, T01 and T17, plus switching roles on the gap page. The other 23 resumes were tested through the same live API, not manually clicked through the UI.
- Four additional stateless controls using empty skills or valid reference skill IDs, with no extra personal data.
- API isolation settings: synthetic two-year break, no activities. Browser settings: displayed “Less than a year,” with synthetic “Managing schedules” activity because the form requires one. These are test inputs, not facts about the resume owners. Both browser snapshots added Scheduling and Coordination; the tested role recommendations and scores matched the API cases.
- Expected occupational families were recorded before live results. Folder labels are **not** ground truth: the agriculture-folder sample is an adult-education teacher, and the automobile-folder sample is a secretary.

Primary API run: 2026-08-30T09:21:57.879226+00:00 to 2026-08-30T09:26:44.490578+00:00 (UTC). Median observed parsing latency: **8.8s**; maximum **17.2s**. Median snapshot: 0.89s; median gap calculation: 0.09s. This is a small sequential functional test, not a load test or SLA measurement.

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

Browser evidence: [false 100% screen](</Users/charlesyi/Documents/ChatGPT/SDG5 Project/ReRouteHer_Resume_Verification_2026-08-30/ui_false_100_readiness.png>); [Village manager screen](</Users/charlesyi/Documents/ChatGPT/SDG5 Project/ReRouteHer_Resume_Verification_2026-08-30/ui_village_manager.png>).

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

T01's Supervisor, Management Information Systems page says **“You meet 1 of 4 requirements”** at 1.4%. The role actually has **32** active requirements. The UI adds one match to only the three returned focus gaps. Across the sample, this formula understates the total for **all 50 non-empty requirement sets**. The 25 empty sets are a different failure and should display “not assessed.” Evidence: [incorrect requirement count screen](</Users/charlesyi/Documents/ChatGPT/SDG5 Project/ReRouteHer_Resume_Verification_2026-08-30/ui_requirement_count.png>).

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
| T01 | IT applications team lead / business intelligence manager | Operation Research Analyst | 100% | 0 |
| T02 | Business systems analyst | Operation Research Analyst | 100% | 0 |
| T03 | Operations research analyst | Online Marketing Specialist | 11.8% | 17 |
| T04 | Senior information technology manager | Technology Manager | 6.7% | 18 |
| T05 | ASP.NET web developer | Management Information Systems (MIS) Analyst | 100% | 0 |
| T06 | Software engineering team lead, Agile/Scrum and web applications | Technical Specialist (.Net) | 0% | 24 |
| T07 | Industrial/chemical engineering intern; manufacturing, quality and process improvement | Manufacturing Supervisor | 43.1% | 39 |
| T08 | Engineering manager in building/hotel maintenance and equipment operations | Railway Station Master | 0% | 22 |
| T09 | Engineering technician in electrical/mechanical test-equipment maintenance | Test Technician | 5% | 17 |
| T10 | Substitute teacher with office-support background | Test Analyst (Information Technology) | 100% | 0 |
| T11 | Teacher with lesson planning and executive/administrative support experience | Instructor Grade U41 | 100% | 0 |
| T12 | English teacher | Teacher, Vocational | 49.1% | 11 |
| T13 | Healthcare/wellness consultant and preventive-health program developer | Sales Representative, Medical | 100% | 0 |
| T14 | Consumer food-business CEO with marketing and sales background | Chief data officer | 6.7% | 16 |
| T15 | Presentation designer | Designer Grade B41 | 20.5% | 19 |
| T16 | Pre-press graphic designer | Designer Grade B41 | 10.5% | 19 |
| T17 | Adult education teacher (agriculture sampling folder) | Instructor Grade U41 | 100% | 0 |
| T18 | Secretary II (automobile sampling folder) | Secretary / Administrative Assistant | 9.6% | 17 |
| T19 | Industrial maintenance mechanic with aircraft A&P background | Track Network Technician | 4% | 19 |
| T20 | Lead digital artist and animator | Technical Artist | 100% | 0 |
| T21 | Project and construction manager | Construction Manager | 53.3% | 27 |
| T22 | Finance coordinator with accounting, ERP master data and financial analyst history | Port Captain | 100% | 0 |
| T23 | Human resources generalist | Secretary / Administrative Assistant | 0% | 17 |
| T24 | Sales associate | Technical Sales Engineer | 0% | 23 |
| T25 | Culinary lecturer/chef instructor, dietitian and food-service operations background | Dietetics Officer Grade U41 | 7.1% | 81 |

## Case review notes

- **T01:** IT/BI leadership mapped to adjacent quantitative analysis, not the actual recent title. Top role has no approved requirements; 100% is invalid. Second role displays 1 of 4 although 32 requirements are scored.
- **T02:** Business-systems analyst mapped to adjacent operations research. Two recommendations have no approved requirements.
- **T03:** Operations research analyst mapped to Online Marketing Specialist; unsupported change of occupational family. Returned top role is a retained four-digit legacy entry.
- **T04:** All parsed titles are company/location placeholders; ICT-management family is recovered by embedding, but detailed seniority/identity is not validated.
- **T05:** ASP.NET developer parsed with university/degree entries as experiences, not the web-development job. Top MIS Analyst match is not the stated work; 100% comes from missing requirements.
- **T06:** Software/.NET family is relevant, but 40 extracted skills overlap none of 24 active core IDs. Thirteen extracted IDs instead occur in the held optional inventory. Some extracted skills are false positives, including Turf Management and Conduct Research on Flora.
- **T07:** Manufacturing supervisor is relevant to prior production work, but does not represent the most recent engineering-intern title. Plywood specialty is unsupported and gets 60% without any matches.
- **T08:** Facilities/building engineering manager mapped to Railway Station Master; railway domain is unsupported. Other suggestions include e-commerce sales and an unscorable assistant-engineer role.
- **T09:** Test Technician is a plausible family for test-equipment maintenance. Ship Technician and Civil Engineering Technician are weak specializations; the ship role has no requirements.
- **T10:** No experiences extracted despite a substitute-teacher work history. Test Analyst (Information Technology) is accepted at 0.018 confidence and assigned 100% from an empty requirement set.
- **T11:** Teacher mapped to Instructor Grade U41, whose ESCO comparison is a low-confidence nursing/midwifery teaching proxy. Treat as unresolved rather than an exact school-teacher match. Secondary CIO/CDO roles are unsupported.
- **T12:** Vocational Teacher is related to teaching but is not a verified English-teacher identity. Four core matches yield 49.1%; nursing/midwifery instructor proxy remains unscorable.
- **T13:** Company/location placeholders replace the healthcare-consultant titles. Medical sales is adjacent to some marketing content, not the stated role; pharmacist grades require evidence not established by this resume test.
- **T14:** Consumer-business CEO mapped to Chief data officer and other ICT chief roles; technical executive identity is not supported by the stated general business background.
- **T15:** Company/location placeholders replace presentation-designer job titles. Broad designer family is plausible, but grade identity is unverified; product-design/ICT-sales additions are weak.
- **T16:** Broad designer family is plausible; Internal Combustion Engine Engineer is an unrelated secondary recommendation. Graphic Designer appears only third.
- **T17:** Adult-education teacher mapped to an unresolved Instructor Grade U41 proxy; Village Community Center Manager reappears second and gets 100% with zero requirements.
- **T18:** Secretary / Administrative Assistant is a relevant retained legacy role, but its MASCO is a four-digit group. Coroner and CIO are unsupported; Coroner gets 40% with zero matches.
- **T19:** Maintenance/aircraft mechanic mapped to railway Track Network Technician; rail specialization is unsupported.
- **T20:** Technical Artist/Graphics Creator are plausible families for a digital artist. All three recommendations are unscorable and each receives 100%.
- **T21:** Construction Manager is a relevant family. It has the highest non-empty top-role score in this sample, 53.3%, but that is still formula coverage, not validated real-world readiness.
- **T22:** Finance coordinator mapped to Port Captain, plus Maintenance Technician and Welding Manager. Port Captain is unscorable at 100%; Welding Manager gets an empty-band baseline of 20%.
- **T23:** Company/location placeholders replace HR titles. Secretarial work is adjacent rather than an exact HR-generalist match; two recommendations use retained four-digit legacy codes.
- **T24:** Retail sales associate mapped to Technical Sales Engineer at 0.235 confidence; no engineering qualification/domain is established. Two additional unscorable roles get 100%.
- **T25:** Dietetics is related to stated nutrition/dietitian history but is not an exact current culinary-lecturer identity. Two dietetics roles share a valid ESCO comparison, not an invalid duplicate. Food and Drinks Technologist is unscorable.

## Evidence, reproducibility and limitations

- [Sample manifest](</Users/charlesyi/Documents/ChatGPT/SDG5 Project/ReRouteHer_Resume_Verification_2026-08-30/sample_manifest.json>): original relative paths, SHA-256 hashes, deterministic seed, category quotas, page/text counts. All 25 selected PDF hashes are distinct.
- [Filtered live results](</Users/charlesyi/Documents/ChatGPT/SDG5 Project/ReRouteHer_Resume_Verification_2026-08-30/live_results.json>): primary HTTP statuses/timings, parsed title fields, skill IDs, recommendations and gap outputs. Full resume text, experience descriptions and contact details were not copied into this evidence file.
- [Reconciliation audit](</Users/charlesyi/Documents/ChatGPT/SDG5 Project/ReRouteHer_Resume_Verification_2026-08-30/audit_results.json>): all 75 role/skill/score checks and catalogue joins; zero formula or matched-skill discrepancies.
- [Four scoring controls](</Users/charlesyi/Documents/ChatGPT/SDG5 Project/ReRouteHer_Resume_Verification_2026-08-30/gap_controls.json>); [Browser observations](</Users/charlesyi/Documents/ChatGPT/SDG5 Project/ReRouteHer_Resume_Verification_2026-08-30/ui_observations.json>); [Manual review notes](</Users/charlesyi/Documents/ChatGPT/SDG5 Project/ReRouteHer_Resume_Verification_2026-08-30/manual_review.json>).
- Reference data: applied `ReRouteHer_Data_Quality_Fix_2026-08-30` release, with the seven retained legacy role fixtures. This was not a fresh full-database duplicate audit. No database connection or mutation was made during verification.
- Relevant inspected source: [scoring](https://github.com/ryus0006/rerouteher-system/blob/23ed6b88a54be269449715656cc51d21c8e8af3b/app/services/gap.py), [PDF extraction](https://github.com/ryus0006/rerouteher-system/blob/23ed6b88a54be269449715656cc51d21c8e8af3b/app/services/cv_extractor.py), [role lookup](https://github.com/ryus0006/rerouteher-system/blob/23ed6b88a54be269449715656cc51d21c8e8af3b/app/repositories/roles.py), [snapshot](https://github.com/ryus0006/rerouteher-system/blob/23ed6b88a54be269449715656cc51d21c8e8af3b/app/services/snapshot.py), [gap display](https://github.com/ryus0006/rerouteher-ui/blob/4e2603812196112cd1807f87388d53e4c5f9709a/src/routes/Gap.jsx), [body logging](https://github.com/ryus0006/rerouteher-system/blob/main/app/core/logging.py). Exact deployed commit was not independently inspected; live responses/browser states are the behavioral evidence.
- Small, deliberately stratified sample; not population accuracy, Malaysia-specific occupational validation, fairness testing, OCR testing, a security audit, or production acceptance. No certified six-digit ground-truth labels or human readiness scores were supplied.
- Original PDFs were not edited or copied into the deliverable. User explicitly approved transmitting them after being informed that parsed content may be retained in application logs. No training occurred, no accounts were created and no server logs were deleted. Temporary browser test CV state was removed after evidence capture; this does not delete server logs.
