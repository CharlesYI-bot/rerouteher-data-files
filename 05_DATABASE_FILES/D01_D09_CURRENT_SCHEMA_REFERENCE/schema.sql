-- LEGACY PGVECTOR SCHEMA REFERENCE ONLY; this file does not load data.
-- For the complete D1-D10 no-pgvector schema plus data, use:
-- ReRouteHer_Complete_D1_D10_NoPgvector.sql (or its .sql.gz version).
-- ReRouteHer high-standard release (PostgreSQL 15+ / pgvector)
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE roles (
  role_id text PRIMARY KEY,
  role_title text NOT NULL,
  masco_code text NOT NULL,
  masco_title text NOT NULL,
  isco08_code text NOT NULL,
  esco_code text NOT NULL,
  onet_code text NOT NULL,
  task_summary text NOT NULL,
  occupation_description text,
  remote_possibility text CHECK (remote_possibility IN ('low','medium','high')),
  ai_exposure text CHECK (ai_exposure IN ('low','medium','high')),
  ai_exposure_share numeric CHECK (ai_exposure_share BETWEEN 0 AND 1),
  flexible_role boolean NOT NULL,
  rating_status text NOT NULL,
  embedding_model text NOT NULL,
  role_embedding vector(384)
);

CREATE TABLE role_tasks (
  masco_task_id text PRIMARY KEY,
  role_id text NOT NULL REFERENCES roles(role_id),
  task_rank integer NOT NULL CHECK (task_rank > 0),
  masco_code text NOT NULL,
  task text NOT NULL,
  source text NOT NULL,
  source_page_pdf integer,
  UNIQUE (role_id, task_rank)
);

CREATE TABLE task_rating_reviews (
  masco_task_id text PRIMARY KEY REFERENCES role_tasks(masco_task_id),
  remote_task_pre_rating text NOT NULL,
  remote_rule_evidence text,
  ai_task_pre_rating text NOT NULL,
  ai_rule_evidence text,
  rating_method text NOT NULL,
  rater_1 text,
  rater_1_rating text,
  rater_2 text,
  rater_2_rating text,
  reconciled_rating text,
  review_status text NOT NULL
);

CREATE TABLE skill_taxonomy (
  skill_id text PRIMARY KEY,
  canonical_name text NOT NULL,
  definition text,
  skill_type text NOT NULL CHECK (skill_type IN ('technical','soft','digital')),
  competence_area text,
  level text,
  source_framework text NOT NULL,
  source_id text,
  embedding_model text NOT NULL,
  embedding vector(384)
);

CREATE TABLE skill_aliases (
  skill_id text NOT NULL REFERENCES skill_taxonomy(skill_id),
  alias text NOT NULL,
  alias_source text NOT NULL,
  PRIMARY KEY (skill_id, alias)
);

CREATE TABLE role_skills (
  role_id text REFERENCES roles(role_id),
  skill_id text REFERENCES skill_taxonomy(skill_id),
  importance numeric CHECK (importance BETWEEN 0 AND 100),
  source text NOT NULL,
  importance_method text NOT NULL,
  curation_note text,
  PRIMARY KEY (role_id, skill_id)
);

CREATE TABLE caregiving_map (
  activity_id text,
  break_activity text NOT NULL,
  mapping_rank integer NOT NULL,
  onet_skill_id text REFERENCES skill_taxonomy(skill_id),
  reframed_label text NOT NULL,
  mapping_method text NOT NULL,
  PRIMARY KEY (activity_id, mapping_rank)
);

CREATE TABLE bursa_sectors (
  sector_id text PRIMARY KEY,
  sector_name text UNIQUE NOT NULL
);

CREATE TABLE employers (
  employer_id text PRIMARY KEY,
  name text NOT NULL,
  sector_id text NOT NULL REFERENCES bursa_sectors(sector_id),
  has_report boolean,
  report_year integer,
  report_url text,
  recognition_score numeric CHECK (recognition_score BETWEEN 0 AND 100),
  gender_equity_score numeric CHECK (gender_equity_score BETWEEN 0 AND 100),
  policy_flex_score numeric CHECK (policy_flex_score BETWEEN 0 AND 100),
  mother_friendly_score numeric CHECK (mother_friendly_score BETWEEN 0 AND 100),
  confidence text,
  score_status text NOT NULL,
  evidence_status text NOT NULL
);

CREATE TABLE role_sector_map (
  role_id text REFERENCES roles(role_id),
  sector_id text REFERENCES bursa_sectors(sector_id),
  mapping_purpose text NOT NULL,
  mapping_method text NOT NULL,
  evidence_basis text,
  rationale text,
  review_status text NOT NULL,
  PRIMARY KEY (role_id, sector_id)
);

CREATE TABLE employer_evidence (
  evidence_id text PRIMARY KEY,
  employer_id text REFERENCES employers(employer_id),
  pillar text NOT NULL,
  fact_field text NOT NULL,
  extracted_value text NOT NULL,
  unit text,
  source_year integer,
  source_url text NOT NULL,
  page_or_section text,
  evidence_paraphrase text,
  verification_status text NOT NULL,
  reviewer text,
  review_date date
);

CREATE TABLE employer_report_search (
  employer_id text PRIMARY KEY REFERENCES employers(employer_id),
  search_status text NOT NULL CHECK (search_status IN ('not_completed','report_located_and_reviewed','completed_no_report_found')),
  has_report boolean,
  report_year integer,
  report_url text,
  recognition_search_status text NOT NULL,
  no_report_zero_rule_applied boolean NOT NULL DEFAULT false,
  search_completion_note text NOT NULL,
  CHECK (NOT no_report_zero_rule_applied OR search_status = 'completed_no_report_found')
);

CREATE TABLE employer_review_queue (
  employer_id text PRIMARY KEY REFERENCES employers(employer_id),
  priority text NOT NULL,
  review_status text NOT NULL,
  checks_required text NOT NULL,
  reviewer text,
  review_date date,
  decision text,
  review_notes text
);

CREATE TABLE release_sources (
  relative_path text PRIMARY KEY,
  sha256 text NOT NULL,
  bytes bigint NOT NULL CHECK (bytes >= 0),
  source_role text NOT NULL,
  acquired_or_generated_on date,
  source_url_or_note text
);
