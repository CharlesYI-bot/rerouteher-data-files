# Review of the three proposed skill SQL files

Decision: **do not run these files unchanged**. No SQL from the attachments was executed against a database. The user's authorization was conditional on the files passing review; they do not pass.

This review uses the attached SQL, the saved database schema, the saved backend source, and the data package associated with today's successful database update. The previous update receipt identifies `rerouteher_test`, schema `rerouteher`. Live database state and the currently deployed backend were not revalidated: no database connector or existing in-app database tab was available in this session. Original attachments are preserved under `originals/`.

## Blocking findings

| File / location | Finding | Required correction |
| --- | --- | --- |
| `ai-usage-band.sql:62,78`; all soft-band INSERTs | Both scripts omit `role_skills.importance_method`. The saved schema declares it NOT NULL with no default. On that schema, an insertion fails and aborts its transaction. | Supply an explicit, truthful rating method on each inserted row; confirm live defaults and triggers. |
| `ai-usage-band.sql:64,80` | Adds `ai_usage`, but saved `GapService._readiness` accepts only technical/soft for role coverage and digital for AI coverage. These new skills contribute to neither coverage calculation; the gap-label code would also label them as role skills. | Coordinate database, backend, API/UI, extraction and lookup support for `ai_usage`, and test its effect on readiness. Do not silently relabel it as digital. |
| `ai-usage-band.sql:29-53` | Skill-master INSERT has no conflict handling. Rerunning it after a successful run fails on the primary key before the role-level NOT EXISTS guards matter. | Use a guarded insert/upsert with a policy for existing IDs and differing content. |
| `ai-usage-band.sql:68-99` | Domain inference reads role_skills without excluding generated or universal additions. Running the soft script first gives every role Coordination and Service Orientation, causing AIUSE_05 to match every role. The software and design patterns also match broad non-development/non-visual skills. Correction on 2026-08-31: the earlier claim that C1 by itself makes every role receive AIUSE_03/04 was incorrect; the SQL matches skill_name, not the descriptions containing draft/data. | Derive domain candidates from a fixed, reviewed set of occupation evidence, excluding generated AI and universal soft additions. Test precision before inserting. |
| `soft-band.sql`, Part A and subsequent NOT EXISTS guards | Reclassifies Active Listening/Speaking in the master only. Existing role links retain their previous type because the INSERT skips existing pairs. Lineage is not synchronized. | Update existing affected links and lineage consistently, preserving their provenance and ratings unless explicitly changing them. |
| All three scripts | Existing data management maintains `role_skill_lineage`. Additions and deletions here do not maintain that companion table or archive before-images. Separate COMMITs can also leave only part of the bundle applied. | Create an auditable migration with a backup, exact before-images, lineage maintenance, validation, rollback rehearsal and one coordinated transaction. |

## Mapping quality concerns

`noise-removal.sql` targets **124 role/skill-name pairs across 12 roles**. All 124 pairs exist in the saved active-core CSV. This is a local candidate count, not a verified live deletion count: actual deletions also depend on the current source guard and current data. `cleanup_candidate_preview.csv` lists every candidate and its resolved saved skill ID.

The casino skills on Game Producer (Digital) and unrelated surgical specialties on Ophthalmic Assistant look like strong review candidates. However, “drop every programming language” from CAD/CAM and AutoCad roles is not sufficiently justified. Lisp, Visual Basic, Python or programming knowledge can have automation uses; their presence alone does not establish leakage. Similarly, scientific research on software roles and statistics on data-entry roles require role-task evidence. The supplied file does not establish that every targeted pair is wrong. Use exact `(role_id, skill_id)` decisions with evidence, a saved before-image and an archive; do not approve all 124 solely from their names.

The source guard protects rows whose source is exactly `curated`, including erroneous curated mappings. It includes NULL sources via `IS DISTINCT FROM`, despite the header describing `<>`; the saved schema currently disallows NULL source values. Neither form validates occupational relevance.

The soft script assigns eight soft skills plus two technical skills to every role at importance 70, and conditionally adds four more soft skills and Mathematics at 60. That is **12 soft skills and 3 technical skills**, not 15 soft skills. Universal Service Orientation, Social Perceptiveness and Complex Problem Solving are modeling assumptions, and can inflate transferable-skill coverage. Weights and requirements should come from role relevance, not a goal of guaranteeing a nonzero match for every user. Preserve these as clearly documented curated assumptions if adopted.

The AI script's comments promise digital-to-technical reclassification, but the executable Part A is absent. Existing digital rows remain unchanged. Blanket movement of all digital skills into technical is itself a modeling decision and should not be inserted as a mechanical repair. The AI skill definitions are project-authored; the current `DigComp 2.2 (AI literacy)` source label should distinguish inspiration from an official framework skill or identifier.

The seven embedded vectors each have 384 finite components and norms approximately 1.0. This verifies their shape and normalization only; it does not prove the claimed model or input text produced them.

## Prepared validation and next step

`READ_ONLY_PREFLIGHT.sql` inspects the live schema/defaults/constraints/triggers, reports all four skill types, identifies master/link mismatches, previews the exact original cleanup predicates with lineage, and reports missing/dangling lineage. It is wrapped in a read-only transaction ending in ROLLBACK. It has been inspected but not run against the database.

The user's coverage query should include an `ai_usage` column and count `rs.skill_id` explicitly; the prepared query does both. Coverage totals alone do not demonstrate that a role-skill mapping is correct.

Before applying a corrected migration: verify the live database and deployed backend; settle role-specific soft/AI requirements and the disputed removal list; preserve existing digital mappings unless separately justified; implement safe conflict handling and lineage updates; back up and rehearse with ROLLBACK; verify unchanged unrelated rows and rerun stability; then commit and test the actual application. No application deployment, service restart, schema edit or database mutation was performed during this review.

Evidence: `ReRouteHer_D13_FINAL_2026-08-30/00_SOURCE_SNAPSHOT/user_existing_schema.sql` (role_skills and skill_taxonomy), `ReRouteHer_Gap_Diagnosis_2026-08-30/source/backend/app/services/gap.py` (coverage and gap classification), `ReRouteHer_Data_Quality_Fix_2026-08-30/01_TABLES/role_skills.csv` (cleanup candidates), and `ReRouteHer_Data_Quality_DB_Update_2026-08-30/live_update_receipt.json` (previous deployment receipt).


## Subsequent execution — 2026-08-31

After explicit user authorization, corrected versions were committed to rerouteher_test through Safari/pgAdmin. See `../ReRouteHer_Skill_SQL_Apply_2026-08-31/` for the migration, receipts and verification. The original scripts remain unchanged. The live schema additionally had two skill-type checks excluding ai_usage; these were widened in the corrected migration. Application support was explicitly excluded by the user.
