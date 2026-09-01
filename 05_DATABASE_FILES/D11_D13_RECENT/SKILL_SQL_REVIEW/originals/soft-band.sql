-- =====================================================================
-- Soft band population (caregiving-transferable skills)
-- Review-and-run script for the data team.
--
-- Context: the soft band in role_skills was empty, so a returning mother's
-- reframed caregiving experience (which resolves to O*NET soft skill ids via
-- caregiving_map) had nothing to match against and always scored zero. This
-- script assigns the exact 15 O*NET skills that caregiving_map reframes to -
-- the only soft skills a returning mother can actually match - onto roles.
-- All 15 already exist in skill_taxonomy with embeddings, so nothing to embed.
--
-- Run order: A (reclassify) -> B (universal core) -> C (relevance-mapped).
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- PART A: Active Listening and Speaking are interpersonal/transferable
-- skills; reclassify them from technical to soft so the soft band reflects
-- them. Remove this statement to keep them technical.
-- ---------------------------------------------------------------------
UPDATE rerouteher.skill_taxonomy SET skill_type = 'soft'
WHERE skill_id IN ('ONET_2_A_1_b','ONET_2_A_1_d');

-- ---------------------------------------------------------------------
-- PART B: universal transferable core -> every role. These are the
-- caregiving reframe targets that apply to virtually any job, so a returning
-- mother's reframed experience always has something to match. importance = 70.
-- (Monitoring and Learning Strategies stay technical, per skill_taxonomy.)
-- ---------------------------------------------------------------------
INSERT INTO rerouteher.role_skills
  (role_id, skill_id, skill_name, skill_type, importance, source, curation_note)
SELECT r.role_id, x.skill_id, x.skill_name, x.skill_type, 70,
       'curated','Soft band (caregiving-transferable core)'
FROM rerouteher.roles r
CROSS JOIN (VALUES
  ('ONET_2_B_1_b','Coordination','soft'),
  ('ONET_2_B_5_a','Time Management','soft'),
  ('ONET_2_A_1_b','Active Listening','soft'),
  ('ONET_2_A_1_d','Speaking','soft'),
  ('ONET_2_B_1_a','Social Perceptiveness','soft'),
  ('ONET_2_B_1_f','Service Orientation','soft'),
  ('ONET_2_B_2_i','Complex Problem Solving','soft'),
  ('ONET_2_B_4_e','Judgment and Decision Making','soft'),
  ('ONET_2_A_2_d','Monitoring','technical'),
  ('ONET_2_A_2_c','Learning Strategies','technical')
) AS x(skill_id, skill_name, skill_type)
WHERE NOT EXISTS (
  SELECT 1 FROM rerouteher.role_skills rs
  WHERE rs.role_id = r.role_id AND rs.skill_id = x.skill_id
);

-- ---------------------------------------------------------------------
-- PART C: relevance-mapped specialists -> roles by MASCO group OR duty text
-- (task_summary + occupation_description). importance = 60. One block per
-- skill so each filter can be reviewed/adjusted. MASCO prefixes: 1 Managers,
-- 12 Admin & Commercial Managers, 21 Science & Engineering Professionals,
-- 23 Teaching Professionals, 25 ICT Professionals, 33 Business & Admin
-- Associate Professionals, 52 Sales Workers, 53 Personal Care Workers.
-- ---------------------------------------------------------------------

-- Negotiation -> managers, sales, business associates
INSERT INTO rerouteher.role_skills (role_id, skill_id, skill_name, skill_type, importance, source, curation_note)
SELECT r.role_id, 'ONET_2_B_1_d','Negotiation','soft', 60, 'curated','Soft band (relevance-mapped)'
FROM rerouteher.roles r
WHERE (r.masco_code LIKE '1%' OR r.masco_code LIKE '33%' OR r.masco_code LIKE '52%'
       OR (COALESCE(r.task_summary,'') || ' ' || COALESCE(r.occupation_description,''))
          ~* '(negotiat|bargain|contract|procure|purchas|sales|sell|persuad|tender)')
AND NOT EXISTS (SELECT 1 FROM rerouteher.role_skills rs WHERE rs.role_id=r.role_id AND rs.skill_id='ONET_2_B_1_d');

-- Instructing -> teaching, care, supervisory
INSERT INTO rerouteher.role_skills (role_id, skill_id, skill_name, skill_type, importance, source, curation_note)
SELECT r.role_id, 'ONET_2_B_1_e','Instructing','soft', 60, 'curated','Soft band (relevance-mapped)'
FROM rerouteher.roles r
WHERE (r.masco_code LIKE '23%' OR r.masco_code LIKE '53%'
       OR (COALESCE(r.task_summary,'') || ' ' || COALESCE(r.occupation_description,''))
          ~* '(teach|train|instruct|tutor|coach|mentor|educat|demonstrat|guide)')
AND NOT EXISTS (SELECT 1 FROM rerouteher.role_skills rs WHERE rs.role_id=r.role_id AND rs.skill_id='ONET_2_B_1_e');

-- Management of Financial Resources -> finance, commercial managers
INSERT INTO rerouteher.role_skills (role_id, skill_id, skill_name, skill_type, importance, source, curation_note)
SELECT r.role_id, 'ONET_2_B_5_b','Management of Financial Resources','soft', 60, 'curated','Soft band (relevance-mapped)'
FROM rerouteher.roles r
WHERE (r.masco_code LIKE '12%'
       OR (COALESCE(r.task_summary,'') || ' ' || COALESCE(r.occupation_description,''))
          ~* '(budget|financ|account|cost|expenditur|fund|revenue|invoic|audit)')
AND NOT EXISTS (SELECT 1 FROM rerouteher.role_skills rs WHERE rs.role_id=r.role_id AND rs.skill_id='ONET_2_B_5_b');

-- Management of Personnel Resources -> managers, supervisors
INSERT INTO rerouteher.role_skills (role_id, skill_id, skill_name, skill_type, importance, source, curation_note)
SELECT r.role_id, 'ONET_2_B_5_d','Management of Personnel Resources','soft', 60, 'curated','Soft band (relevance-mapped)'
FROM rerouteher.roles r
WHERE (r.masco_code LIKE '1%'
       OR (COALESCE(r.task_summary,'') || ' ' || COALESCE(r.occupation_description,''))
          ~* '(supervis|manage staff|lead.{0,10}team|personnel|human resource|recruit|delegat|oversee)')
AND NOT EXISTS (SELECT 1 FROM rerouteher.role_skills rs WHERE rs.role_id=r.role_id AND rs.skill_id='ONET_2_B_5_d');

-- Mathematics -> engineering, science, finance, analytics (stays technical)
INSERT INTO rerouteher.role_skills (role_id, skill_id, skill_name, skill_type, importance, source, curation_note)
SELECT r.role_id, 'ONET_2_A_1_e','Mathematics (O*NET Skill)','technical', 60, 'curated','Soft band (relevance-mapped)'
FROM rerouteher.roles r
WHERE (r.masco_code LIKE '21%' OR r.masco_code LIKE '25%'
       OR (COALESCE(r.task_summary,'') || ' ' || COALESCE(r.occupation_description,''))
          ~* '(calculat|mathemat|statistic|numeric|arithmetic|quantitativ|formula)')
AND NOT EXISTS (SELECT 1 FROM rerouteher.role_skills rs WHERE rs.role_id=r.role_id AND rs.skill_id='ONET_2_A_1_e');

COMMIT;
