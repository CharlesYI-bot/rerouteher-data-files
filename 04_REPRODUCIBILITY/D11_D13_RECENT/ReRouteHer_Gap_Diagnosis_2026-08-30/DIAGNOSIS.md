# ReRouteHer gap diagnosis — 30 August 2026

## Conclusion

This is a combined D13 suitability, taxonomy integration, role resolution and scoring problem—not a Title Case problem. MASCO roles and ESCO occupations must not be treated as interchangeable identities. Keeping ESCO comparison codes is correct; using a shared comparison code as a unique MASCO lookup is not.

Diagnosis only: no database rows, schema, application code, models or deployments were changed. New local files are diagnostic evidence and isolated source snapshots. Live SQL was run with `default_transaction_read_only=on` and a 15-second statement timeout. API probes used synthetic, non-personal inputs and calculation-only endpoints.

## Evidence checked

- Current GitHub backend commit: `23ed6b88a54be269449715656cc51d21c8e8af3b`.
- Current GitHub frontend commit: `4e2603812196112cd1807f87388d53e4c5f9709a`.
- Live app API and the existing Safari gap/snapshot pages.
- Live Coolify `postgresql-database-wxnjpd2ia8avtwbs739mtamk`, database `rerouteher_test`, schema `rerouteher`.
- Released D13 MASCO 2020 CSVs and the earlier migration receipt.
- Bundled `ml/tfidf_logreg.joblib`: local Git blob hash exactly matches current GitHub (`53b04ad2954bcc8462382e9ae1feed6db27bdb1a`). Its catalog contains 2,980 ESCO occupations and 2,980 four-digit candidate codes, not a six-digit MASCO role classifier. Local model probes emitted a scikit-learn version warning (artifact 1.7.2, local 1.9.0); primary behavioral conclusions below are independently supported by live API results. The exact deployed Git commit was not inspected in deployment logs.

## 1. Wrong MASCO role selected from a shared ESCO code — high priority

The snapshot resolves an ESCO prediction by `esco_code` first. The repository query is `WHERE esco_code = :c LIMIT 1`, with no ordering, context ranking, mapping confidence or relationship check.

- Synthetic live input **Software Developer** returned **Technical Specialist (.Net)** as the previous occupation at confidence 0.839. Both share ESCO `2512.4`; the D13 Software Developer role is actually MASCO `251201`, whereas the selected specialist is `251116`.
- **Village Community Center Manager**, MASCO `151108`, is one of seven live MASCO roles sharing ESCO `1330.5` (ICT Operations Manager). Its D13 relation is explicitly `partial_proxy`, confidence `low`. The app ignores those warnings.
- The other six are Technology Manager, Information Systems Manager, Data Operations Manager, Network Manager, Information Technology Infrastructure Manager, and Network Operations Manager. These are not identical jobs merely because the comparison occupation is shared.
- In the release, 422 of 655 roles participate in 143 shared-ESCO groups; there are only 376 distinct selected ESCO occupations. This ambiguity is widespread.

The SQL does not guarantee which row wins; it is not necessarily random on every request, but can change with data layout or query plans. Separately, the four-digit fallback selects the lowest matching MASCO prefix, rather than identifying the correct six-digit role.

Sources: [role lookup](https://github.com/ryus0006/rerouteher-system/blob/23ed6b88a54be269449715656cc51d21c8e8af3b/app/repositories/roles.py#L41), [resolution order](https://github.com/ryus0006/rerouteher-system/blob/23ed6b88a54be269449715656cc51d21c8e8af3b/app/services/snapshot.py#L267), [bundled matcher](https://github.com/ryus0006/rerouteher-system/blob/23ed6b88a54be269449715656cc51d21c8e8af3b/app/services/occupation_matcher.py).

## 2. Weak or unrelated recommendations are not rejected — high priority

The configured occupation confidence threshold is not used to reject final recommendations. A weak classifier/retrieval result can be accepted; the service also fills the list to three using nearest embeddings without a minimum relevance threshold. The top recommendation is assigned `similarity=1.0` even when the underlying match is weak. Classifier-resolved roles do not pass the same flexible-role filter used by embedding retrieval.

Live synthetic checks:

| Input | Returned recommendations |
|---|---|
| Software Developer | Technical Specialist (.Net), Application Development Manager, Computer Programmer |
| IT Manager, with IT operations/network/cybersecurity description | Mining Excecutive (confidence 0.386), Technology Manager, Information Systems Manager |
| ICT Operations Manager | Technology Manager, Manufacturing Manager, Railway and Locomotive Operation Officer |

The existing Safari snapshot showed Teacher, Vocational at about 48% confidence, with Instructor Grade U41 and Village Community Center Manager in the gap selector. The exact historical request/server log was not retrieved, so the specific branch that introduced Village in that cached result cannot be conclusively distinguished. Both shared-ESCO resolution and unthresholded recommendation filling are available paths. D13 also marks Village as flexible based on inherited preliminary task ratings, so it is eligible for the embedding pool.

Sources: [recommendation construction](https://github.com/ryus0006/rerouteher-system/blob/23ed6b88a54be269449715656cc51d21c8e8af3b/app/services/snapshot.py#L226), [settings](https://github.com/ryus0006/rerouteher-system/blob/23ed6b88a54be269449715656cc51d21c8e8af3b/app/config.py), [fallback matching](https://github.com/ryus0006/rerouteher-system/blob/23ed6b88a54be269449715656cc51d21c8e8af3b/app/services/occupation_matcher.py).

## 3. D13 optional skill inventories became mandatory readiness denominators — high priority

The fast test dataset imported all essential and optional skills of the chosen ESCO occupation. Essential links weigh 100; optional links weigh 50. The gap engine includes both in the denominator and calls every uncovered item a gap. ESCO optional skills often describe alternative specialisms, not requirements every person must meet simultaneously.

The exact live teacher example is confirmed in the database:

- `M232102` Teacher, Vocational → ESCO `2320.1` Vocational Teacher.
- **115 skills = 11 essential + 104 optional**.
- Optional skills include aircraft flight controls, locomotive brakes, nursing, boating, and other subject specialisms.
- The live page showed **3.3% readiness**, four matched skills, and top gaps Aircraft Flight Control Systems, Technology Education, Electronics.

This is not evidence that the person is only 3.3% capable. It measures a small set of extracted exact matches against an overbroad, uncalibrated inventory.

The band weighting amplifies the error. For this role, the technical band totals 6,100 weight and the digital band only 200. At low AI exposure (20% digital weight):

- One optional aircraft skill contributes `20 × 50 / 200 = 5` percentage points.
- One essential technical/teaching skill contributes `80 × 100 / 6100 ≈ 1.31` points.

Thus the irrelevant aircraft skill outranks essential teaching requirements. D13's coarse digital/technical compatibility classification was not a validated AI-readiness taxonomy. In addition, 78 D13 roles have no digital band; the current scorer treats an empty band as fully covered, creating inconsistent baseline scores.

The earlier source/schema checks verified faithful import and referential integrity, not role-specific skill relevance or readiness calibration. The fast test D13 release should not have been treated as a validated assessment specification.

Source: [gap formula and ranking](https://github.com/ryus0006/rerouteher-system/blob/23ed6b88a54be269449715656cc51d21c8e8af3b/app/services/gap.py#L35).

## 4. Exact skill-ID matching exposes missing IDs and mixed taxonomies — high priority

Canonical skill IDs are the right basis for identity, but all upstream paths must actually supply the same canonical concept IDs. Currently:

- The gap engine ignores skill names and accepts only exact supplied `skill_id` values.
- Live control: Python + SQL + JavaScript with valid ESCO IDs, targeting Technical Specialist (.Net), scored **1.7%**. The same names without IDs scored **0%**.
- That software profile contains 108 skills (24 essential, 84 optional), so three recognized optional digital skills contribute only `60 × 150 / 5450 ≈ 1.65%`.
- The career-break skill schema has no `skill_id`; those skills therefore cannot contribute to this scorer.
- Old persisted browser snapshots may lack IDs. The guest-state persistence version is still 1, without a dataset/model version check.
- D1 O*NET/DigComp skills coexist with ESCO leaf concepts. A recognized O*NET skill is not automatically the corresponding ESCO UUID.
- The alias dictionary chooses the first ID for a colliding term using `setdefault`, with no contextual disambiguation or explicit priority. There are 175 ambiguous alias labels in the combined live DB (172 within the new D13 aliases).

This is not fixed by changing capitalization or by giving fuzzy credit indiscriminately. IDs must be normalized through reviewed equivalences, missing IDs must be surfaced, and ambiguous aliases need disambiguation.

Sources: [ID-only scoring](https://github.com/ryus0006/rerouteher-system/blob/23ed6b88a54be269449715656cc51d21c8e8af3b/app/services/gap.py#L26), [break skill schema](https://github.com/ryus0006/rerouteher-system/blob/23ed6b88a54be269449715656cc51d21c8e8af3b/app/schemas/snapshot.py), [alias dictionary selection](https://github.com/ryus0006/rerouteher-system/blob/23ed6b88a54be269449715656cc51d21c8e8af3b/app/services/snapshot.py#L82), [persisted state](https://github.com/ryus0006/rerouteher-ui/blob/4e2603812196112cd1807f87388d53e4c5f9709a/src/store/intakeStore.js).

## 5. Duplicate audit: distinguish D13 from the combined live database

| Check | D13 release only | Combined live database |
|---|---:|---:|
| Roles | 655 | 665 |
| Repeated normalized role titles | 0 | 2 groups |
| Repeated MASCO codes | 0 | 0 |
| Shared ESCO codes | 143 groups | 144 groups |
| Repeated normalized canonical skill labels | 0 | 2 groups |
| Repeated `(role_id, skill_id)` pairs | 0 | 0 |
| Ambiguous alias labels across IDs | 172 | 175 |

Live duplicate titles:

- Data Analyst: `R02` / MASCO `2524`, and `M252403` / MASCO `252403`.
- Graphic Designer: `R06` / MASCO `2543`, and `M254302` / MASCO `254302`.

Live repeated canonical skill labels:

- Mathematics: `ONET_2_A_1_e` and ESCO UUID `4339176e-3acd-4f7f-a5d9-445bee3d23f2`.
- Programming: `DIGCOMP_3_4` and `ONET_2_B_3_e`.

Mathematics also occurs under both IDs in `role_skills`. Matching display labels do not alone establish full conceptual equivalence across frameworks; definitions should be reviewed before selecting a canonical ID and remapping references.

Within D13, the same canonical skill consistently reuses the same ID across roles: no name-to-multiple-ID or ID-to-multiple-name discrepancies, no repeated role-skill pairs. A live join also found zero D13 role-skill label mismatches against `skill_taxonomy`.

The live original rows remain at four-digit group level, except `R01`, which at audit time was named `duplicate` with MASCO and ESCO both `0`. This differs from the earlier migration receipt; its author/timing was not investigated. No changes were made to it during this diagnosis. These legacy rows should not silently participate as valid six-digit MASCO roles.

**Do not deduplicate distinct MASCO roles solely because ESCO codes repeat.** That would discard valid role identities to conceal a many-to-one comparison. Keep a unique MASCO role catalog and reusable canonical skill catalog; allow shared comparison codes with explicit relationship/confidence and provenance.

## 6. Frontend requirement count is incorrect

The page displays `matched skills + returned gaps` as the total. The backend returns only the top three gaps, so “4 of 7 requirements” actually refers to four matches plus three displayed recommendations, not all 115 skills considered by the scorer. This explains why the displayed fraction looks incompatible with 3.3%.

Source: [display denominator](https://github.com/ryus0006/rerouteher-ui/blob/4e2603812196112cd1807f87388d53e4c5f9709a/src/routes/Gap.jsx#L99).

## Recommended correction order — not implemented

1. Resolve and return a stable six-digit MASCO role ID; do not select a role with `ESCO LIMIT 1`, group-prefix first-row fallback, or a role-title lookup. Rank actual MASCO candidates using title, tasks, context and validated relationship evidence; allow no suitable match.
2. Keep ESCO comparison links, but honor close/broader/partial status. Do not propagate a predicted ESCO confidence as confidence in a more specific MASCO role. Do not force three weak recommendations.
3. Build a relevant core skill requirement set for each MASCO role. Treat ESCO optional specialisms as conditional suggestions, not universal deficits. Calibrate the digital band and score against representative profiles before labelling it readiness.
4. Reconcile legacy D1 roles and overlapping skill concepts with explicit reference remapping, preserving unrelated records and provenance. Do not merge distinct concepts just because their names match. Preserve shared skill IDs in role-skill links.
5. Carry canonical skill IDs end-to-end, including reviewed career-break mappings; resolve ambiguous aliases; invalidate stale caches/snapshots by dataset version. Report insufficient evidence rather than silently interpreting missing IDs as no capability.
6. Return a real requirement total and matched count separately from the top-three focus list. Add regression tests for the observed teacher, software-developer and IT-manager cases, duplicate titles, partial mappings, missing IDs, empty bands and optional specialisms.

The immediate need is not blindly retraining or deleting repeated ESCO codes. Correct the data-to-scoring contract and role-identity resolution first; then evaluate whether a six-digit MASCO matcher needs retraining. Any resume-based evaluation/training should continue to use only the approved JobHop v2 2019+ dataset.
