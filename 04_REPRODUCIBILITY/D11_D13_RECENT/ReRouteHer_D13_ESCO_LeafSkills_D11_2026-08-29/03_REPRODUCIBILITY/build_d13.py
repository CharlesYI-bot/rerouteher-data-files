#!/usr/bin/env python3
"""Build D13 ESCO leaf-skill tables for the D11 six-digit MASCO scope.

The build is deliberately conservative. Existing D11 ESCO codes are retained.
For D11 roles without a code, an ESCO occupation is selected only when the
normalised D11 title has a unique exact match to an ESCO preferred or alternate
label inside the same four-digit ISCO group. Fuzzy candidates are review-only.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import shutil
import unicodedata
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from sentence_transformers import SentenceTransformer


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EXPECTED_D11_ROLES = 657
EXPECTED_DIMENSIONS = 384
OFFICIAL_DOWNLOAD_URL = "https://esco.ec.europa.eu/en/use-esco/download"
OFFICIAL_STRUCTURE_URL = "https://esco.ec.europa.eu/en/structure-esco-downloadable-datasets"

ROOT = Path(__file__).resolve().parents[1]
TABLE_DIR = ROOT / "01_TABLES"
QA_DIR = ROOT / "02_QA"
SOURCE_DIR = ROOT / "00_SOURCE_SNAPSHOT"
MODEL_DIR = ROOT / "05_MODEL_ARTIFACTS"


def parse_args() -> argparse.Namespace:
    workspace = ROOT.parent
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--d11-roles",
        type=Path,
        default=workspace
        / "ReRouteHer_D11_STEM_2026-08-29"
        / "01_TABLES"
        / "D11_STEM_roles.csv",
    )
    parser.add_argument(
        "--esco-dir",
        type=Path,
        default=Path(
            "/Users/charlesyi/Downloads/ESCO dataset - v1.2.1 - classification - en - csv"
        ),
    )
    parser.add_argument(
        "--esco-zip",
        type=Path,
        default=Path(
            "/Users/charlesyi/Downloads/ESCO dataset - v1.2.1 - classification - en - csv.zip"
        ),
    )
    parser.add_argument(
        "--brief-docx",
        type=Path,
        default=Path(
            "/Users/charlesyi/Downloads/Copy of Data Team Tasks - ReRouteHer (Iteration 1).docx"
        ),
    )
    parser.add_argument("--model", default=MODEL_NAME)
    parser.add_argument("--allow-model-download", action="store_true")
    return parser.parse_args()


def normalise(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode()
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def latest_by_uri(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], int]:
    latest: dict[str, dict[str, str]] = {}
    duplicates = 0
    for row in rows:
        uri = row["conceptUri"]
        if uri in latest:
            duplicates += 1
        if uri not in latest or row.get("modifiedDate", "") > latest[uri].get("modifiedDate", ""):
            latest[uri] = row
    return list(latest.values()), duplicates


def title_alignment(role_title: str, occupation: dict[str, str]) -> str:
    role_norm = normalise(role_title)
    if role_norm == normalise(occupation["preferredLabel"]):
        return "exact_preferred_label"
    if role_norm in {normalise(label) for label in occupation["altLabels"].splitlines() if label.strip()}:
        return "exact_alternate_label"
    return "non_exact_title"


def best_label_similarity(role_title: str, occupation: dict[str, str]) -> tuple[float, str, str]:
    role_norm = normalise(role_title)
    labels = [(occupation["preferredLabel"], "preferredLabel")]
    labels.extend((label, "altLabel") for label in occupation["altLabels"].splitlines() if label.strip())
    best_score, best_label, best_type = -1.0, "", ""
    for label, label_type in labels:
        score = SequenceMatcher(None, role_norm, normalise(label)).ratio()
        if score > best_score:
            best_score, best_label, best_type = score, label, label_type
    return best_score, best_label, best_type


def skill_id(uri: str) -> str:
    return uri.rstrip("/").rsplit("/", 1)[-1]


def effective_skill_type(row: dict[str, str]) -> str:
    """Preserve ESCO skillType, making official blank DigComp values explicit."""
    if row["skillType"].strip():
        return row["skillType"].strip()
    if "concept-scheme/digcomp" in row.get("inScheme", ""):
        return "esco_unspecified_digcomp"
    return "esco_unspecified"


def pgvector(values: np.ndarray) -> str:
    return "[" + ",".join(f"{float(value):.8f}" for value in values) + "]"


def make_mapping(
    roles: list[dict[str, str]], occupations: list[dict[str, str]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, dict[str, str]]]:
    by_code = {row["code"]: row for row in occupations}
    by_group: dict[str, list[dict[str, str]]] = defaultdict(list)
    preferred: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    alternate: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for occupation in occupations:
        group = occupation["iscoGroup"]
        by_group[group].append(occupation)
        preferred[(group, normalise(occupation["preferredLabel"]))].append(occupation)
        for label in occupation["altLabels"].splitlines():
            if label.strip():
                alternate[(group, normalise(label))].append(occupation)

    coverage: list[dict[str, Any]] = []
    review_rows: list[dict[str, Any]] = []
    chosen_by_role: dict[str, dict[str, str]] = {}

    for role in roles:
        role_id = role["role_id"]
        group = role["masco_unit_group_code"]
        role_norm = normalise(role["role_title"])
        d11_code = role["esco_code"].strip()
        selected: dict[str, str] | None = None
        mapping_status = ""
        mapping_method = ""
        mapping_authority = ""
        review_status = "manual_mapping_required"
        coverage_note = ""

        if d11_code:
            selected = by_code.get(d11_code)
            if selected:
                mapping_status = "d11_existing_esco_code"
                mapping_method = "Retained the ESCO code supplied in the D11 dataset."
                mapping_authority = role.get("esco_crosswalk_status", "project crosswalk")
                review_status = "pending_domain_owner_review"
                coverage_note = (
                    "Used provisionally because it is part of D11; title alignment is reported separately."
                )
            else:
                mapping_status = "d11_esco_code_not_in_v1_2_1"
                mapping_method = "D11 code failed the ESCO v1.2.1 occupations lookup."
                mapping_authority = role.get("esco_crosswalk_status", "project crosswalk")
                coverage_note = "Not used in D13 role_skills."
        else:
            preferred_matches = preferred[(group, role_norm)]
            alternate_matches = alternate[(group, role_norm)]
            if len(preferred_matches) == 1:
                selected = preferred_matches[0]
                mapping_status = "unique_exact_preferred_title_same_isco_group"
                mapping_method = "Unique normalised exact preferred-label match within the same four-digit group."
                mapping_authority = "official eMASCO title + official ESCO v1.2.1 occupation label; project-derived crosswalk"
                review_status = "pending_domain_owner_review"
                coverage_note = "Provisionally usable; not an official published MASCO-to-ESCO crosswalk."
            elif len(alternate_matches) == 1:
                selected = alternate_matches[0]
                mapping_status = "unique_exact_alternate_title_same_isco_group"
                mapping_method = "Unique normalised exact alternate-label match within the same four-digit group."
                mapping_authority = "official eMASCO title + official ESCO v1.2.1 alternate label; project-derived crosswalk"
                review_status = "pending_domain_owner_review"
                coverage_note = "Provisionally usable; alternate-label match requires domain-owner review."
            elif len(preferred_matches) > 1 or len(alternate_matches) > 1:
                mapping_status = "ambiguous_exact_title_same_isco_group"
                mapping_method = "Multiple exact ESCO title or alias matches; no code selected."
                mapping_authority = "official eMASCO title + official ESCO v1.2.1 labels"
                coverage_note = "Not used; manual choice required."
            else:
                mapping_status = "no_unique_exact_esco_title_match"
                mapping_method = "No exact preferred or alternate ESCO title match in the same four-digit group."
                mapping_authority = "official eMASCO title + official ESCO v1.2.1 labels"
                coverage_note = (
                    "Not used; the D1 parent ESCO code is not inherited to a distinct six-digit child role."
                )

        chosen_code = selected["code"] if selected else ""
        alignment = title_alignment(role["role_title"], selected) if selected else ""
        similarity, matched_label, matched_label_type = (
            best_label_similarity(role["role_title"], selected) if selected else (0.0, "", "")
        )
        if selected:
            chosen_by_role[role_id] = selected

        coverage.append(
            {
                "role_id": role_id,
                "role_title": role["role_title"],
                "masco_code": role["masco_code"],
                "masco_code_printed": role["masco_code_printed"],
                "masco_unit_group_code": group,
                "d11_esco_code": d11_code,
                "d11_esco_comparison_codes": role.get("esco_comparison_codes", ""),
                "chosen_esco_code": chosen_code,
                "chosen_esco_title": selected["preferredLabel"] if selected else "",
                "chosen_esco_uri": selected["conceptUri"] if selected else "",
                "chosen_esco_isco_group": selected["iscoGroup"] if selected else "",
                "mapping_status": mapping_status,
                "mapping_method": mapping_method,
                "mapping_authority": mapping_authority,
                "title_match_type": alignment,
                "title_match_score": f"{similarity:.6f}" if selected else "",
                "review_status": review_status,
                "use_in_role_skills": str(bool(selected)),
                "production_ready": "False",
                "coverage_note": coverage_note,
            }
        )

        if selected:
            review_rows.append(
                {
                    "role_id": role_id,
                    "role_title": role["role_title"],
                    "masco_code": role["masco_code"],
                    "masco_unit_group_code": group,
                    "candidate_rank": 1,
                    "candidate_esco_code": selected["code"],
                    "candidate_esco_title": selected["preferredLabel"],
                    "candidate_esco_uri": selected["conceptUri"],
                    "matched_label": matched_label,
                    "matched_label_type": matched_label_type,
                    "title_similarity": f"{similarity:.6f}",
                    "candidate_status": "provisionally_used_pending_review",
                    "mapping_status": mapping_status,
                    "review_decision": "",
                    "reviewer": "",
                    "review_notes": "",
                }
            )
        else:
            candidates: list[tuple[float, dict[str, str], str, str]] = []
            for occupation in by_group.get(group, []):
                score, label, label_type = best_label_similarity(role["role_title"], occupation)
                candidates.append((score, occupation, label, label_type))
            candidates.sort(key=lambda item: (-item[0], item[1]["code"]))
            for rank, (score, occupation, label, label_type) in enumerate(candidates[:3], 1):
                review_rows.append(
                    {
                        "role_id": role_id,
                        "role_title": role["role_title"],
                        "masco_code": role["masco_code"],
                        "masco_unit_group_code": group,
                        "candidate_rank": rank,
                        "candidate_esco_code": occupation["code"],
                        "candidate_esco_title": occupation["preferredLabel"],
                        "candidate_esco_uri": occupation["conceptUri"],
                        "matched_label": label,
                        "matched_label_type": label_type,
                        "title_similarity": f"{score:.6f}",
                        "candidate_status": "review_only_not_used",
                        "mapping_status": mapping_status,
                        "review_decision": "",
                        "reviewer": "",
                        "review_notes": "",
                    }
                )
            if not candidates:
                review_rows.append(
                    {
                        "role_id": role_id,
                        "role_title": role["role_title"],
                        "masco_code": role["masco_code"],
                        "masco_unit_group_code": group,
                        "candidate_rank": "",
                        "candidate_esco_code": "",
                        "candidate_esco_title": "",
                        "candidate_esco_uri": "",
                        "matched_label": "",
                        "matched_label_type": "",
                        "title_similarity": "",
                        "candidate_status": "no_esco_occupation_in_same_isco_group",
                        "mapping_status": mapping_status,
                        "review_decision": "",
                        "reviewer": "",
                        "review_notes": "",
                    }
                )

    return coverage, review_rows, chosen_by_role


def main() -> None:
    args = parse_args()
    source_paths = {
        "skills_en.csv": args.esco_dir / "skills_en.csv",
        "occupationSkillRelations_en.csv": args.esco_dir / "occupationSkillRelations_en.csv",
        "occupations_en.csv": args.esco_dir / "occupations_en.csv",
    }
    for path in [args.d11_roles, *source_paths.values()]:
        if not path.exists():
            raise FileNotFoundError(path)

    for directory in [TABLE_DIR, QA_DIR, SOURCE_DIR, MODEL_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
    copied_source_dir = SOURCE_DIR / "ESCO_v1.2.1_classification_en_csv"
    copied_source_dir.mkdir(parents=True, exist_ok=True)
    for name, path in source_paths.items():
        shutil.copy2(path, copied_source_dir / name)
    if args.esco_zip.exists():
        shutil.copy2(args.esco_zip, SOURCE_DIR / args.esco_zip.name)

    roles = read_csv(args.d11_roles)
    if len(roles) != EXPECTED_D11_ROLES:
        raise AssertionError(f"Expected {EXPECTED_D11_ROLES} D11 roles, got {len(roles)}")

    occupation_rows_raw = read_csv(source_paths["occupations_en.csv"])
    occupations, occupation_duplicate_rows = latest_by_uri(occupation_rows_raw)
    skill_rows_raw = read_csv(source_paths["skills_en.csv"])
    skills, skill_duplicate_rows = latest_by_uri(skill_rows_raw)
    relations = read_csv(source_paths["occupationSkillRelations_en.csv"])

    coverage, review_rows, chosen_by_role = make_mapping(roles, occupations)
    coverage_by_role = {row["role_id"]: row for row in coverage}
    selected_occupation_uris = {row["conceptUri"] for row in chosen_by_role.values()}
    scoped_relations = [row for row in relations if row["occupationUri"] in selected_occupation_uris]
    relation_by_occupation: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in scoped_relations:
        relation_by_occupation[row["occupationUri"]].append(row)

    skills_by_uri = {row["conceptUri"]: row for row in skills}
    scoped_skill_uris = {row["skillUri"] for row in scoped_relations}
    missing_skill_uris = sorted(scoped_skill_uris - set(skills_by_uri))
    if missing_skill_uris:
        raise AssertionError(f"ESCO relations reference missing skills: {missing_skill_uris[:5]}")
    scoped_skills = sorted(
        (skills_by_uri[uri] for uri in scoped_skill_uris),
        key=lambda row: (row["preferredLabel"].casefold(), row["conceptUri"]),
    )

    embedding_inputs = []
    for row in scoped_skills:
        definition = row["definition"].strip() or row["description"].strip()
        embedding_inputs.append(
            f"{row['preferredLabel']}. {definition}" if definition else row["preferredLabel"]
        )
    encoder = SentenceTransformer(args.model, local_files_only=not args.allow_model_download)
    vectors = encoder.encode(
        embedding_inputs,
        batch_size=64,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=True,
    )
    if vectors.shape != (len(scoped_skills), EXPECTED_DIMENSIONS):
        raise AssertionError(f"Unexpected embedding shape {vectors.shape}")

    taxonomy_rows: list[dict[str, Any]] = []
    taxonomy_lineage_rows: list[dict[str, Any]] = []
    for row, vector, embedding_text in zip(scoped_skills, vectors, embedding_inputs):
        sid = skill_id(row["conceptUri"])
        definition = row["definition"].strip() or row["description"].strip()
        taxonomy_rows.append(
            {
                "skill_id": sid,
                "canonical_name": row["preferredLabel"],
                "definition": definition,
                "skill_type": effective_skill_type(row),
                "embedding": pgvector(vector),
            }
        )
        taxonomy_lineage_rows.append(
            {
                "skill_id": sid,
                "concept_uri": row["conceptUri"],
                "preferred_label": row["preferredLabel"],
                "skill_type": effective_skill_type(row),
                "official_skill_type_raw": row["skillType"],
                "reuse_level": row["reuseLevel"],
                "status": row["status"],
                "modified_date": row["modifiedDate"],
                "definition_source_field": "definition" if row["definition"].strip() else "description",
                "embedding_text": embedding_text,
                "embedding_model": args.model,
                "embedding_dimensions": EXPECTED_DIMENSIONS,
                "l2_normalized": "True",
                "source_version": "ESCO v1.2.1",
            }
        )

    alias_rows: list[dict[str, str]] = []
    alias_seen: set[tuple[str, str]] = set()

    def add_alias(sid: str, canonical: str, alias: str, source: str) -> None:
        cleaned = " ".join(alias.split())
        key = (sid, cleaned.casefold())
        if not cleaned or cleaned.casefold() == canonical.casefold() or key in alias_seen:
            return
        alias_seen.add(key)
        alias_rows.append({"skill_id": sid, "alias": cleaned, "alias_source": source})

    curated: dict[str, list[str]] = {
        "use spreadsheets software": ["Excel", "MS Excel", "spreadsheets"],
        "JavaScript": ["JS", "Java Script"],
        "SQL": ["Structured Query Language"],
    }
    for row in scoped_skills:
        sid = skill_id(row["conceptUri"])
        canonical = row["preferredLabel"]
        for alias in row["altLabels"].splitlines():
            add_alias(sid, canonical, alias, "esco_altLabel")
        for alias in row["hiddenLabels"].splitlines():
            add_alias(sid, canonical, alias, "esco_hiddenLabel")
        for alias in curated.get(canonical, []):
            add_alias(sid, canonical, alias, "curated_product_or_acronym")
    alias_rows.sort(key=lambda row: (row["skill_id"], row["alias"].casefold(), row["alias_source"]))

    role_skill_rows: list[dict[str, Any]] = []
    role_skill_lineage_rows: list[dict[str, Any]] = []
    role_by_id = {row["role_id"]: row for row in roles}
    for role_id in sorted(chosen_by_role):
        role = role_by_id[role_id]
        occupation = chosen_by_role[role_id]
        mapping = coverage_by_role[role_id]
        for relation in sorted(
            relation_by_occupation[occupation["conceptUri"]],
            key=lambda row: (row["skillLabel"].casefold(), row["skillUri"]),
        ):
            sid = skill_id(relation["skillUri"])
            official_skill = skills_by_uri[relation["skillUri"]]
            importance = 100 if relation["relationType"] == "essential" else 50
            role_skill_rows.append(
                {
                    "role_id": role_id,
                    "skill_id": sid,
                    "skill_name": official_skill["preferredLabel"],
                    "skill_type": effective_skill_type(official_skill),
                    "importance": importance,
                }
            )
            role_skill_lineage_rows.append(
                {
                    "role_id": role_id,
                    "role_title": role["role_title"],
                    "masco_code": role["masco_code"],
                    "esco_code": occupation["code"],
                    "esco_occupation_title": occupation["preferredLabel"],
                    "esco_occupation_uri": occupation["conceptUri"],
                    "mapping_status": mapping["mapping_status"],
                    "mapping_review_status": mapping["review_status"],
                    "skill_id": sid,
                    "skill_uri": relation["skillUri"],
                    "skill_name": official_skill["preferredLabel"],
                    "relation_type": relation["relationType"],
                    "skill_type": effective_skill_type(official_skill),
                    "importance": importance,
                    "source_version": "ESCO v1.2.1",
                    "production_ready": "False",
                }
            )

    coverage_columns = [
        "role_id", "role_title", "masco_code", "masco_code_printed", "masco_unit_group_code",
        "d11_esco_code", "d11_esco_comparison_codes", "chosen_esco_code", "chosen_esco_title",
        "chosen_esco_uri", "chosen_esco_isco_group", "mapping_status", "mapping_method",
        "mapping_authority", "title_match_type", "title_match_score", "review_status",
        "use_in_role_skills", "production_ready", "coverage_note",
    ]
    review_columns = [
        "role_id", "role_title", "masco_code", "masco_unit_group_code", "candidate_rank",
        "candidate_esco_code", "candidate_esco_title", "candidate_esco_uri", "matched_label",
        "matched_label_type", "title_similarity", "candidate_status", "mapping_status",
        "review_decision", "reviewer", "review_notes",
    ]
    write_csv(TABLE_DIR / "D13_role_esco_coverage.csv", coverage, coverage_columns)
    write_csv(TABLE_DIR / "D13_role_esco_mapping_review.csv", review_rows, review_columns)
    write_csv(
        TABLE_DIR / "skill_taxonomy.csv",
        taxonomy_rows,
        ["skill_id", "canonical_name", "definition", "skill_type", "embedding"],
    )
    write_csv(
        TABLE_DIR / "skill_taxonomy_lineage.csv",
        taxonomy_lineage_rows,
        [
            "skill_id", "concept_uri", "preferred_label", "skill_type", "official_skill_type_raw", "reuse_level", "status",
            "modified_date", "definition_source_field", "embedding_text", "embedding_model",
            "embedding_dimensions", "l2_normalized", "source_version",
        ],
    )
    write_csv(TABLE_DIR / "skill_aliases.csv", alias_rows, ["skill_id", "alias", "alias_source"])
    write_csv(
        TABLE_DIR / "role_skills.csv",
        role_skill_rows,
        ["role_id", "skill_id", "skill_name", "skill_type", "importance"],
    )
    write_csv(
        TABLE_DIR / "role_skills_lineage.csv",
        role_skill_lineage_rows,
        [
            "role_id", "role_title", "masco_code", "esco_code", "esco_occupation_title",
            "esco_occupation_uri", "mapping_status", "mapping_review_status", "skill_id",
            "skill_uri", "skill_name", "relation_type", "skill_type", "importance",
            "source_version", "production_ready",
        ],
    )

    np.save(MODEL_DIR / "D13_skill_embeddings.npy", vectors.astype(np.float32))
    write_csv(
        MODEL_DIR / "D13_skill_embedding_index.csv",
        [{"embedding_index": i, "skill_id": skill_id(row["conceptUri"])} for i, row in enumerate(scoped_skills)],
        ["embedding_index", "skill_id"],
    )
    norms = np.linalg.norm(vectors, axis=1)
    write_json(
        MODEL_DIR / "D13_embedding_model.json",
        {
            "model": args.model,
            "dimensions": EXPECTED_DIMENSIONS,
            "l2_normalized": True,
            "input_format": "preferredLabel. definition (description used when definition is blank)",
            "skill_count": len(scoped_skills),
            "min_l2_norm": float(norms.min()),
            "max_l2_norm": float(norms.max()),
        },
    )

    source_manifest_rows = []
    for name, path in source_paths.items():
        source_manifest_rows.append(
            {
                "source_id": name.replace(".csv", ""),
                "source_name": name,
                "source_version": "ESCO v1.2.1",
                "authority": "European Commission ESCO",
                "source_url": OFFICIAL_DOWNLOAD_URL,
                "local_input_path": str(path),
                "release_snapshot_path": str((copied_source_dir / name).relative_to(ROOT)),
                "sha256": sha256(path),
                "rows": len(read_csv(path)),
                "usage": "D13 official leaf-skill source",
            }
        )
    source_manifest_rows.append(
        {
            "source_id": "d11_roles",
            "source_name": args.d11_roles.name,
            "source_version": "D11 2026-08-29",
            "authority": "ReRouteHer D11 derived from official eMASCO",
            "source_url": "https://emasco.mohr.gov.my",
            "local_input_path": str(args.d11_roles),
            "release_snapshot_path": "",
            "sha256": sha256(args.d11_roles),
            "rows": len(roles),
            "usage": "User-authoritative replacement for D1 role scope",
        }
    )
    if args.brief_docx.exists():
        source_manifest_rows.append(
            {
                "source_id": "d13_task_brief",
                "source_name": args.brief_docx.name,
                "source_version": "Iteration 1 D13 release brief",
                "authority": "User-provided project brief; instructions interpreted under explicit user override",
                "source_url": "",
                "local_input_path": str(args.brief_docx),
                "release_snapshot_path": "",
                "sha256": sha256(args.brief_docx),
                "rows": "",
                "usage": "D13 specification only",
            }
        )
    write_csv(
        QA_DIR / "D13_source_manifest.csv",
        source_manifest_rows,
        [
            "source_id", "source_name", "source_version", "authority", "source_url",
            "local_input_path", "release_snapshot_path", "sha256", "rows", "usage",
        ],
    )

    status_counts = Counter(row["mapping_status"] for row in coverage)
    alias_source_counts = Counter(row["alias_source"] for row in alias_rows)
    summary = {
        "scope_override": "D13 references to D1 were applied to the D11 catalog of 657 official six-digit MASCO roles.",
        "d11_role_count": len(roles),
        "six_digit_masco_role_count": sum(bool(re.fullmatch(r"\d{6}", row["masco_code"])) for row in roles),
        "roles_with_provisional_esco_mapping": len(chosen_by_role),
        "roles_without_usable_esco_mapping": len(roles) - len(chosen_by_role),
        "role_mapping_coverage_rate": round(len(chosen_by_role) / len(roles), 6),
        "mapping_status_counts": dict(sorted(status_counts.items())),
        "distinct_esco_occupations_used": len(selected_occupation_uris),
        "scoped_leaf_skills": len(taxonomy_rows),
        "skill_alias_rows": len(alias_rows),
        "alias_source_counts": dict(sorted(alias_source_counts.items())),
        "role_skill_rows": len(role_skill_rows),
        "essential_role_skill_rows": sum(row["importance"] == 100 for row in role_skill_rows),
        "optional_role_skill_rows": sum(row["importance"] == 50 for row in role_skill_rows),
        "embedding_model": args.model,
        "embedding_dimensions": EXPECTED_DIMENSIONS,
        "l2_normalized": True,
        "esco_source_version": "v1.2.1",
        "esco_source_skill_rows": len(skill_rows_raw),
        "esco_unique_skill_uris": len(skills),
        "esco_duplicate_skill_rows_deduplicated_by_latest_modifiedDate": skill_duplicate_rows,
        "esco_skills_with_blank_official_skillType_made_explicit": sum(
            not row["skillType"].strip() for row in scoped_skills
        ),
        "esco_source_occupation_rows": len(occupation_rows_raw),
        "esco_unique_occupation_uris": len(occupations),
        "esco_duplicate_occupation_rows_deduplicated_by_latest_modifiedDate": occupation_duplicate_rows,
        "esco_relation_rows": len(relations),
        "scope_guard": "Only leaf skills linked to provisionally mapped D11 roles are included; the full ESCO skill universe is excluded.",
        "production_warning": "No published official MASCO-six-digit-to-ESCO-occupation crosswalk exists in the supplied sources. All project-derived mappings remain pending domain-owner review.",
    }
    write_json(QA_DIR / "D13_build_summary.json", summary)

    checks = [
        ("d11_role_count_657", len(roles) == EXPECTED_D11_ROLES, len(roles)),
        ("all_masco_codes_six_digits", all(re.fullmatch(r"\d{6}", row["masco_code"]) for row in roles), len(roles)),
        ("unique_role_ids", len({row["role_id"] for row in roles}) == len(roles), len({row["role_id"] for row in roles})),
        ("coverage_has_all_d11_roles", len(coverage) == len(roles), len(coverage)),
        ("chosen_esco_codes_exist_officially", all(row["code"] in {o["code"] for o in occupations} for row in chosen_by_role.values()), len(chosen_by_role)),
        ("role_skill_importance_is_essential_or_optional", {row["importance"] for row in role_skill_rows} <= {50, 100}, sorted({row["importance"] for row in role_skill_rows})),
        ("role_skill_pairs_unique", len({(row["role_id"], row["skill_id"]) for row in role_skill_rows}) == len(role_skill_rows), len(role_skill_rows)),
        ("taxonomy_matches_linked_skills", {row["skill_id"] for row in taxonomy_rows} == {row["skill_id"] for row in role_skill_rows}, len(taxonomy_rows)),
        ("skill_types_nonblank", all(row["skill_type"] for row in taxonomy_rows), Counter(row["skill_type"] for row in taxonomy_rows)),
        ("mapping_review_represents_all_roles", len({row["role_id"] for row in review_rows}) == len(roles), len({row["role_id"] for row in review_rows})),
        ("aliases_unique_case_insensitive", len(alias_seen) == len(alias_rows), len(alias_rows)),
        ("embedding_dimension_384", vectors.shape[1] == EXPECTED_DIMENSIONS, vectors.shape[1]),
        ("embeddings_l2_normalized", bool(np.allclose(norms, 1.0, atol=1e-5)), {"min": float(norms.min()), "max": float(norms.max())}),
        ("scope_excludes_full_esco_skill_universe", len(taxonomy_rows) < len(skills), {"scoped": len(taxonomy_rows), "official_unique": len(skills)}),
        ("no_fuzzy_candidates_used", all(row["mapping_status"] != "no_unique_exact_esco_title_match" for row in coverage if row["use_in_role_skills"] == "True"), len(chosen_by_role)),
    ]
    write_csv(
        QA_DIR / "D13_validation_checks.csv",
        [
            {"check_id": check_id, "status": "PASS" if passed else "FAIL", "observed": json.dumps(observed, ensure_ascii=False)}
            for check_id, passed, observed in checks
        ],
        ["check_id", "status", "observed"],
    )
    failed = [check_id for check_id, passed, _ in checks if not passed]
    if failed:
        raise AssertionError(f"D13 QA failed: {failed}")

    output_paths = sorted(
        path for path in ROOT.rglob("*")
        if path.is_file()
        and path.name != "D13_OUTPUT_SHA256SUMS.txt"
        and "00_SOURCE_SNAPSHOT" not in path.parts
        and "__pycache__" not in path.parts
    )
    checksum_lines = [f"{sha256(path)}  {path.relative_to(ROOT)}" for path in output_paths]
    (ROOT / "D13_OUTPUT_SHA256SUMS.txt").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
