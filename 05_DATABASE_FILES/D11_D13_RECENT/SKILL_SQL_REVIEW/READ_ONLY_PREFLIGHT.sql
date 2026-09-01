-- READ ONLY. No original migration is executed by this file.
-- The previous successful update targeted rerouteher_test; verify the intended
-- environment before any future write. Run with psql -v ON_ERROR_STOP=1.
BEGIN READ ONLY;
SET LOCAL statement_timeout = '30s';
SELECT current_database() AS database_name, current_schema() AS default_schema;
SELECT table_name,column_name,data_type,udt_name,is_nullable,column_default
FROM information_schema.columns
WHERE table_schema='rerouteher' AND table_name IN ('role_skills','skill_taxonomy')
ORDER BY table_name,ordinal_position;
SELECT conrelid::regclass AS table_name,conname,pg_get_constraintdef(oid)
FROM pg_constraint WHERE connamespace='rerouteher'::regnamespace;
SELECT tgrelid::regclass AS table_name,tgname,pg_get_triggerdef(oid)
FROM pg_trigger WHERE tgrelid IN ('rerouteher.role_skills'::regclass,'rerouteher.skill_taxonomy'::regclass)
AND NOT tgisinternal;
SELECT r.role_id,r.role_title,r.masco_code,r.ai_exposure,
 count(rs.skill_id) AS total,
 count(rs.skill_id) FILTER (WHERE rs.skill_type='technical') AS technical,
 count(rs.skill_id) FILTER (WHERE rs.skill_type='soft') AS soft,
 count(rs.skill_id) FILTER (WHERE rs.skill_type='digital') AS digital,
 count(rs.skill_id) FILTER (WHERE rs.skill_type='ai_usage') AS ai_usage,
 count(rs.skill_id) FILTER (WHERE rs.skill_type IS NULL OR rs.skill_type NOT IN ('technical','soft','digital','ai_usage')) AS other
FROM rerouteher.roles r LEFT JOIN rerouteher.role_skills rs USING(role_id)
GROUP BY r.role_id,r.role_title,r.masco_code,r.ai_exposure ORDER BY r.role_title;
SELECT rs.role_id,rs.skill_id,rs.skill_name,rs.skill_type,t.canonical_name,t.skill_type AS taxonomy_type
FROM rerouteher.role_skills rs LEFT JOIN rerouteher.skill_taxonomy t USING(skill_id)
WHERE rs.skill_name IS DISTINCT FROM t.canonical_name OR rs.skill_type IS DISTINCT FROM t.skill_type;
SELECT skill_id,canonical_name,skill_type FROM rerouteher.skill_taxonomy
WHERE starts_with(skill_id,'AIUSE_') OR skill_id IN ('ONET_2_A_1_b','ONET_2_A_1_d');
-- Exact preview of the original cleanup predicates, including source protection.
WITH candidates AS (
 SELECT * FROM rerouteher.role_skills WHERE
(source IS DISTINCT FROM 'curated' AND role_id='M251116' AND skill_name IN ('Perform Scientific Research','Engineering Principles','Engineering Processes','Manage Engineering Project','Technical Drawings','Use Technical Drawing Software'))
 OR (source IS DISTINCT FROM 'curated' AND role_id='M251201' AND skill_name IN ('Perform Scientific Research','Engineering Principles','Engineering Processes','Manage Engineering Project','Technical Drawings','Use Technical Drawing Software'))
 OR (source IS DISTINCT FROM 'curated' AND role_id='M251401' AND skill_name IN ('Perform Scientific Research','Engineering Principles','Engineering Processes','Manage Engineering Project','Technical Drawings','Use Technical Drawing Software'))
 OR (source IS DISTINCT FROM 'curated' AND role_id='M251419' AND skill_name IN ('Perform Scientific Research','Engineering Principles','Engineering Processes','Manage Engineering Project','Technical Drawings','Use Technical Drawing Software'))
 OR (source IS DISTINCT FROM 'curated' AND role_id='M251916' AND skill_name IN ('Engineering Processes'))
 OR (source IS DISTINCT FROM 'curated' AND role_id='M252401' AND skill_name IN ('Speak Different Languages'))
 OR (source IS DISTINCT FROM 'curated' AND role_id='M254204' AND skill_name IN ('Manage Gambling Finances','Manage Gaming Facilities','Manage Gambling Game','Follow Ethical Code of Conduct of Gambling','Ensure Gambling Operational Standards','Responsible Gambling','Manage Gaming Cash Desk','Manage Gambling Hospitality'))
 OR (source IS DISTINCT FROM 'curated' AND role_id IN ('M311538','M311544') AND skill_name IN ('Lisp','Visual Basic','Java (Computer Programming)','Computer Programming','Prolog (Computer Programming)','OpenEdge Advanced Business Language','JavaScript','Perl','Use Automatic Programming','Smalltalk (Computer Programming)','PHP','Assembly (Computer Programming)','C#','R','Groovy','ASP.NET','APL','Haskell','Erlang','SAS Language','Ruby (Computer Programming)','Common Lisp','Microsoft Visual C++','TypeScript','CoffeeScript','Objective-C','ML (Computer Programming)','AJAX','C++','SAP R3','Swift (Computer Programming)','MATLAB','Python (Computer Programming)','Scratch (Computer Programming)','VBScript','COBOL','ABAP','Pascal (Computer Programming)','Scala'))
 OR (source IS DISTINCT FROM 'curated' AND role_id='M321204' AND skill_name IN ('Machine Learning','Human-Robot Collaboration','Internet of Things','Principles of Artificial Intelligence','Virtual Reality','Predictive Maintenance'))
 OR (source IS DISTINCT FROM 'curated' AND role_id='M325614' AND skill_name IN ('Operate Patients with Thoracic Diseases','Assist in Epilepsy Surgery','Perform Reconstructive Plastic Surgery'))
 OR (source IS DISTINCT FROM 'curated' AND role_id='M413209' AND skill_name IN ('Resource Description Framework Query Language','Query Languages','Apply Statistical Analysis Techniques'))
)
SELECT c.*,r.role_title,l.review_status,l.one_line_justification
FROM candidates c JOIN rerouteher.roles r USING(role_id)
LEFT JOIN rerouteher.role_skill_lineage l USING(role_id,skill_id)
ORDER BY c.role_id,c.skill_name;
SELECT rs.role_id,rs.skill_id FROM rerouteher.role_skills rs
LEFT JOIN rerouteher.role_skill_lineage l USING(role_id,skill_id) WHERE l.role_id IS NULL;
SELECT l.role_id,l.skill_id FROM rerouteher.role_skill_lineage l
LEFT JOIN rerouteher.role_skills rs USING(role_id,skill_id) WHERE rs.role_id IS NULL;
ROLLBACK;
