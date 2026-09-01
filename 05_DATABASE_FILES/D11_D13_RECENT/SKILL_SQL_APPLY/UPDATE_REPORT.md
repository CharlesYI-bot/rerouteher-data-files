# Skill-band database update — committed and verified

Executed in Safari / pgAdmin against **rerouteher_test**, schema **rerouteher**, at **2026-08-31 00:36:22 Malaysia time**. The three attachments were combined into one corrected transaction. The originals were not edited. No application, deployment, credentials, or Coolify settings were changed; app compatibility was excluded at the user's request.

## Results

| Metric | Result |
| --- | ---: |
| Roles retained | 662 |
| New AI master skills | 7 |
| New AI-usage role mappings | 2,269 |
| New mappings from soft-band script | 7,868 |
| Of those, soft mappings | 6,280 |
| Of those, technical mappings | 1,588 |
| Existing role mappings reclassified for Listening/Speaking | 14 |
| Authorized cleanup mappings removed | 124 |
| Final master skills | 6,128 |
| Final role mappings / matching lineage rows | 23,279 / 23,279 |

Final bands: **6,329 soft**, **2,269 ai_usage**, **2,047 digital**, **12,634 technical**. Every role has the eight core soft skills and the two universal AI-usage skills. Existing ratings on preexisting links were preserved.

AI coverage by skill: everyday work **662**; output verification **662**; data analysis **324**; documents **223**; communication/service **267**; coding **24**; design/visual content **107**.

## Corrections applied

- Rolled back the failed AI insertion already open in pgAdmin.
- Widened only `skill_taxonomy_skill_type_check` and `role_skills_skill_type_check` to accept `ai_usage` alongside the existing three types.
- Supplied the required `importance_method` values, explicitly labeling soft weights as project assumptions rather than O*NET occupational ratings.
- Retained the supplied soft-band role-selection and 70/60 importance rules.
- Reclassified Active Listening and Speaking consistently in the master, existing role mappings and lineage.
- Used original technical/digital evidence for AI-domain matching, excluding generated additions and the approved cleanup candidates. Narrowed generic software/design matches so ordinary software use does not by itself imply AI coding, and nonvisual design does not by itself imply image generation.
- Kept all seven supplied AI embeddings and corrected source attribution to project-curated AI usage inspired by DigComp.
- Resolved the cleanup names to exact role/skill IDs; retained the original `source <> curated` protection using `IS DISTINCT FROM`.
- Applied all 124 user-authorized cleanup targets and removed the corresponding active lineage. No roles or master skills were deleted. The dedicated digital-rating-lineage table had no targeted rows and remained unchanged.
- Preserved existing digital mappings except the 95 digital links explicitly included in cleanup. No blanket digital-to-technical conversion was made. The other 29 cleanup links were technical.
- Added conflict protection and archived full before/after images for recovery and audit.

The cleanup list and universal soft requirements remain user-authorized test curation, not independently validated occupation requirements. A duplicate database backup was reported by the user; it was not independently restored or tested.

## Verification

The rollback rehearsal succeeded in approximately 6.7 seconds. A second mutation pass inserted/deleted zero rows, and all four affected-table fingerprints were unchanged. The identical SQL, differing only in its final COMMIT, then committed in approximately 7.3 seconds.

Independent read-only verification matched the committed receipt's four table fingerprints, found no master/link or lineage mismatch, confirmed all constraints were validated, and confirmed soft/AI coverage for all 662 roles. Its ending ROLLBACK closed only the verification transaction; the earlier migration remains committed.

Full changed-row archives are in `rerouteher.dataset_metadata` under `skill_bands_fix_20260831.role_skills`, `.role_skill_lineage`, `.digital_skill_rating_lineage`, and `.skill_taxonomy`. Each value has `before` and `after` arrays. Original constraint definitions are in `.constraints`, and the committed counts/time/hashes are in `.receipt`. Restoring these later must check for intervening changes before overwriting rows.

Files: `APPLY.sql` (executed), `REHEARSE.sql`, `VERIFY.sql`, `live_receipt.json`, `SHA256SUMS.txt`, and the saved UI outputs.

## Correction to the initial review

The earlier claim that AIUSE_01/02 automatically triggered data/document mappings was incorrect: the original SQL matches skill names, not their descriptions. The real universal contamination occurs if the soft-band script first adds Coordination/Service Orientation to every role. Both generated-band exclusion and narrower software/design matching are implemented in the executed version. The earlier review document was amended to record this correction.
