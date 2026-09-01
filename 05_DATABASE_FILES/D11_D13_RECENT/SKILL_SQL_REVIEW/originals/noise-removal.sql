-- =====================================================================
-- Noise removal for role_skills (accessible re-entry families + IT)
-- Review-and-run script for the data team.
--
-- Scope: MASCO 22x (nursing), 23x (teaching), 25x/35x (IT), 3x/4x/5x
-- (technicians, clerical, service/sales) - the families returning-mother
-- users actually target. Removes skills clearly foreign to the role
-- (engineering/CAD/research leaks on software, over-advanced ICT/data
-- skills on clerical roles, cross-specialty leaks).
--
-- Each DELETE is scoped to one role_id + exact skill_name, and guarded
-- with source <> 'curated' so the curated soft/AI-usage additions are
-- never touched. Curated by per-role review, conservative: only clear
-- mismatches; anything plausibly relevant is kept.
-- =====================================================================

BEGIN;

-- Software-developer family (ESCO 2512.4): engineering/CAD/research leaks
DELETE FROM rerouteher.role_skills WHERE source IS DISTINCT FROM 'curated' AND role_id='M251116' AND skill_name IN ('Perform Scientific Research','Engineering Principles','Engineering Processes','Manage Engineering Project','Technical Drawings','Use Technical Drawing Software');
DELETE FROM rerouteher.role_skills WHERE source IS DISTINCT FROM 'curated' AND role_id='M251201' AND skill_name IN ('Perform Scientific Research','Engineering Principles','Engineering Processes','Manage Engineering Project','Technical Drawings','Use Technical Drawing Software');
DELETE FROM rerouteher.role_skills WHERE source IS DISTINCT FROM 'curated' AND role_id='M251401' AND skill_name IN ('Perform Scientific Research','Engineering Principles','Engineering Processes','Manage Engineering Project','Technical Drawings','Use Technical Drawing Software');
DELETE FROM rerouteher.role_skills WHERE source IS DISTINCT FROM 'curated' AND role_id='M251419' AND skill_name IN ('Perform Scientific Research','Engineering Principles','Engineering Processes','Manage Engineering Project','Technical Drawings','Use Technical Drawing Software');

-- IT Auditor (M251916): engineering-process leak
DELETE FROM rerouteher.role_skills WHERE source IS DISTINCT FROM 'curated' AND role_id='M251916' AND skill_name IN ('Engineering Processes');
-- Data Scientist (M252401): multilingualism leak (translator skill on a research role)
DELETE FROM rerouteher.role_skills WHERE source IS DISTINCT FROM 'curated' AND role_id='M252401' AND skill_name IN ('Speak Different Languages');
-- Game Producer, Digital (M254204): wrong-occupation gambling/casino skills
DELETE FROM rerouteher.role_skills WHERE source IS DISTINCT FROM 'curated' AND role_id='M254204' AND skill_name IN ('Manage Gambling Finances','Manage Gaming Facilities','Manage Gambling Game','Follow Ethical Code of Conduct of Gambling','Ensure Gambling Operational Standards','Responsible Gambling','Manage Gaming Cash Desk','Manage Gambling Hospitality');

-- CAD/CAM Technician (M311538) and AutoCad Drafter (M311544): entire ESCO
-- programming-languages collection dumped on a CAD role. Keep CAD/design tools;
-- drop every programming language.
DELETE FROM rerouteher.role_skills WHERE source IS DISTINCT FROM 'curated' AND role_id IN ('M311538','M311544') AND skill_name IN ('Lisp','Visual Basic','Java (Computer Programming)','Computer Programming','Prolog (Computer Programming)','OpenEdge Advanced Business Language','JavaScript','Perl','Use Automatic Programming','Smalltalk (Computer Programming)','PHP','Assembly (Computer Programming)','C#','R','Groovy','ASP.NET','APL','Haskell','Erlang','SAS Language','Ruby (Computer Programming)','Common Lisp','Microsoft Visual C++','TypeScript','CoffeeScript','Objective-C','ML (Computer Programming)','AJAX','C++','SAP R3','Swift (Computer Programming)','MATLAB','Python (Computer Programming)','Scratch (Computer Programming)','VBScript','COBOL','ABAP','Pascal (Computer Programming)','Scala');

-- Ecology Technician (M321204): advanced-tech/AI bundle foreign to ecology fieldwork
DELETE FROM rerouteher.role_skills WHERE source IS DISTINCT FROM 'curated' AND role_id='M321204' AND skill_name IN ('Machine Learning','Human-Robot Collaboration','Internet of Things','Principles of Artificial Intelligence','Virtual Reality','Predictive Maintenance');
-- Ophthalmic Assistant (M325614): surgeries from unrelated specialties
DELETE FROM rerouteher.role_skills WHERE source IS DISTINCT FROM 'curated' AND role_id='M325614' AND skill_name IN ('Operate Patients with Thoracic Diseases','Assist in Epilepsy Surgery','Perform Reconstructive Plastic Surgery');
-- Data Entry Clerk (M413209): over-advanced query/stats skills for a data-entry role
DELETE FROM rerouteher.role_skills WHERE source IS DISTINCT FROM 'curated' AND role_id='M413209' AND skill_name IN ('Resource Description Framework Query Language','Query Languages','Apply Statistical Analysis Techniques');

COMMIT;
