# ReRouteHer D13 — ESCO leaf skills for the D11 MASCO scope

This release implements D13 using the user-authoritative D11 catalog in place of every D1 dependency. The role scope is therefore 657 official eMASCO occupations identified by six-digit MASCO codes, not the original ten four-digit D1 groups.

The current conservative build links 95 of the 657 roles to 93 ESCO occupations and materializes 2,575 leaf skills, 15,203 aliases, and 5,851 role-skill rows. The other 562 roles stay visible in the coverage and review tables rather than receiving invented ESCO codes.

## What is included

- `01_TABLES/skill_taxonomy.csv`: concrete ESCO v1.2.1 leaf skills linked to provisionally mapped D11 roles, with normalized 384-dimensional all-MiniLM-L6-v2 embeddings.
- `01_TABLES/skill_aliases.csv`: official ESCO alternate and hidden labels plus the small curated acronym/product aliases requested in D13.
- `01_TABLES/role_skills.csv`: the D13 contract (`role_id`, `skill_id`, `skill_name`, `skill_type`, `importance`), using 100 for essential and 50 for optional.
- `01_TABLES/D13_role_esco_coverage.csv`: all 657 D11 roles, their six-digit MASCO codes, retained ESCO comparison fields, selected ESCO occupation where available, mapping method, and review state.
- `01_TABLES/D13_role_esco_mapping_review.csv`: review candidates. Fuzzy candidates are never used to create role-skill links.
- `01_TABLES/*_lineage.csv`: source URIs, ESCO relation types, mapping state, embedding provenance, and production-readiness flags.
- `05_MODEL_ARTIFACTS/`: float32 embedding matrix, stable skill index, and model metadata.
- `04_DATABASE/D13_schema_and_load.sql`: an isolated `rerouteher_d13` PostgreSQL/pgvector schema and loader. It does not overwrite the superseded D2/D6 tables.
- `02_QA/`: source manifest, build summary, and executable validation results.

## Mapping policy and coverage

ESCO publishes occupation-to-skill relations and maps each ESCO occupation to an ISCO-08 group, but the supplied official sources do not contain a published MASCO-six-digit-to-ESCO-occupation crosswalk. D11 itself contains seven project ESCO codes, all marked as pending domain-owner review.

The conservative D13 expansion therefore uses an ESCO occupation only when either:

1. the code already exists in D11 and is present in the ESCO v1.2.1 occupation file; or
2. the normalized D11 role title has one unique exact match to an ESCO preferred or alternate label inside the same four-digit group.

No D1 parent ESCO code is inherited to a different D11 child occupation. Ambiguous and fuzzy matches remain review-only. All selected mappings remain `production_ready=False` until a domain owner approves them.

Four of the seven ESCO codes already present in D11 do not have an exact D11-title-to-ESCO-label alignment. They are retained because D11 is the user-specified dependency, but they are explicitly flagged and should be reviewed first; the release does not present them as official mappings.

## Source and scope guard

The leaf-skill source is the official English `ESCO dataset - v1.2.1 - classification - en - csv` package. This release does not use `ESCO_v1.2.1_skills_occupations_matrix.xlsx`, because that workbook contains occupation × skill-group features rather than the concrete leaf skills required by D13.

Only skills connected to provisionally mapped D11 roles are materialized. The full ESCO skill universe is deliberately excluded. ESCO is EU-centric and English labels may not cover Malaysian terminology; local aliases and human validation should be added before production use.

Three scoped DigComp concepts have blank `skillType` values in the official ESCO source. The release exposes these as `esco_unspecified_digcomp` while preserving the blank official value in `skill_taxonomy_lineage.csv`; it does not silently coerce them to `knowledge` or `skill/competence`.

## Rebuild

The build requires the three official ESCO CSV files and a local copy of `sentence-transformers/all-MiniLM-L6-v2`:

```bash
python3 -m pip install -r 03_REPRODUCIBILITY/requirements.txt
python3 03_REPRODUCIBILITY/build_d13.py
python3 03_REPRODUCIBILITY/validate_d13.py
```

To import into PostgreSQL with pgvector, run from this release directory:

```bash
psql "$DATABASE_URL" -f 04_DATABASE/D13_schema_and_load.sql
```

The MAI similarity threshold retune mentioned in the D13 brief is an application-team step. It is intentionally not performed by this data release.
