\set ON_ERROR_STOP on

-- Run from the D13 release root:
--   psql "$DATABASE_URL" -f 04_DATABASE/D13_schema_and_load.sql
-- The isolated schema prevents D13 from overwriting the superseded D2/D6 tables
-- until the data owner approves the ESCO mappings.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE SCHEMA IF NOT EXISTS rerouteher_d13;

CREATE TABLE IF NOT EXISTS rerouteher_d13.skill_taxonomy (
    skill_id text PRIMARY KEY,
    canonical_name text NOT NULL,
    definition text NOT NULL,
    skill_type text NOT NULL,
    embedding vector(384) NOT NULL
);

CREATE TABLE IF NOT EXISTS rerouteher_d13.skill_aliases (
    skill_id text NOT NULL REFERENCES rerouteher_d13.skill_taxonomy(skill_id) ON DELETE CASCADE,
    alias text NOT NULL,
    alias_source text NOT NULL,
    PRIMARY KEY (skill_id, alias)
);

CREATE TABLE IF NOT EXISTS rerouteher_d13.role_skills (
    role_id text NOT NULL,
    skill_id text NOT NULL REFERENCES rerouteher_d13.skill_taxonomy(skill_id) ON DELETE CASCADE,
    skill_name text NOT NULL,
    skill_type text NOT NULL,
    importance smallint NOT NULL CHECK (importance IN (50, 100)),
    PRIMARY KEY (role_id, skill_id)
);

CREATE TABLE IF NOT EXISTS rerouteher_d13.role_esco_coverage (
    role_id text PRIMARY KEY,
    role_title text NOT NULL,
    masco_code char(6) NOT NULL CHECK (masco_code ~ '^[0-9]{6}$'),
    masco_code_printed text,
    masco_unit_group_code char(4) NOT NULL,
    d11_esco_code text,
    d11_esco_comparison_codes text,
    chosen_esco_code text,
    chosen_esco_title text,
    chosen_esco_uri text,
    chosen_esco_isco_group text,
    mapping_status text NOT NULL,
    mapping_method text NOT NULL,
    mapping_authority text NOT NULL,
    title_match_type text,
    title_match_score double precision,
    review_status text NOT NULL,
    use_in_role_skills boolean NOT NULL,
    production_ready boolean NOT NULL,
    coverage_note text NOT NULL
);

TRUNCATE TABLE rerouteher_d13.role_skills;
TRUNCATE TABLE rerouteher_d13.skill_aliases;
TRUNCATE TABLE rerouteher_d13.skill_taxonomy;
TRUNCATE TABLE rerouteher_d13.role_esco_coverage;

\copy rerouteher_d13.skill_taxonomy (skill_id, canonical_name, definition, skill_type, embedding) FROM '01_TABLES/skill_taxonomy.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
\copy rerouteher_d13.skill_aliases (skill_id, alias, alias_source) FROM '01_TABLES/skill_aliases.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
\copy rerouteher_d13.role_skills (role_id, skill_id, skill_name, skill_type, importance) FROM '01_TABLES/role_skills.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');
\copy rerouteher_d13.role_esco_coverage (role_id, role_title, masco_code, masco_code_printed, masco_unit_group_code, d11_esco_code, d11_esco_comparison_codes, chosen_esco_code, chosen_esco_title, chosen_esco_uri, chosen_esco_isco_group, mapping_status, mapping_method, mapping_authority, title_match_type, title_match_score, review_status, use_in_role_skills, production_ready, coverage_note) FROM '01_TABLES/D13_role_esco_coverage.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');

CREATE INDEX IF NOT EXISTS d13_skill_alias_lower_idx
    ON rerouteher_d13.skill_aliases (lower(alias));
CREATE INDEX IF NOT EXISTS d13_role_skills_role_idx
    ON rerouteher_d13.role_skills (role_id, importance DESC);
CREATE INDEX IF NOT EXISTS d13_role_skills_skill_idx
    ON rerouteher_d13.role_skills (skill_id);
CREATE INDEX IF NOT EXISTS d13_coverage_masco_idx
    ON rerouteher_d13.role_esco_coverage (masco_code);
CREATE INDEX IF NOT EXISTS d13_coverage_esco_idx
    ON rerouteher_d13.role_esco_coverage (chosen_esco_code);

ANALYZE rerouteher_d13.skill_taxonomy;
ANALYZE rerouteher_d13.skill_aliases;
ANALYZE rerouteher_d13.role_skills;
ANALYZE rerouteher_d13.role_esco_coverage;

SELECT 'skill_taxonomy' AS table_name, count(*) AS row_count FROM rerouteher_d13.skill_taxonomy
UNION ALL SELECT 'skill_aliases', count(*) FROM rerouteher_d13.skill_aliases
UNION ALL SELECT 'role_skills', count(*) FROM rerouteher_d13.role_skills
UNION ALL SELECT 'role_esco_coverage', count(*) FROM rerouteher_d13.role_esco_coverage;
