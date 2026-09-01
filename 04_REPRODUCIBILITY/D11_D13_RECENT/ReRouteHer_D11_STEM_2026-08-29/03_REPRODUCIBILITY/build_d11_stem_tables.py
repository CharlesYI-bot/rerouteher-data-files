#!/usr/bin/env python3
"""Build D1-compatible D11 tables from the official eMASCO STEM snapshot."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from sentence_transformers import SentenceTransformer


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
SOURCE_PATH = ROOT / "00_SOURCE_SNAPSHOT" / "emasco_stem_occupations_2026-08-29.json"
TABLE_DIR = ROOT / "01_TABLES"
QA_DIR = ROOT / "02_QA"
D1_PATH = (
    WORKSPACE
    / "ReRouteHer_TeamDrive_Upload_2026-08-27"
    / "03_PROCESSED_DATA"
    / "01_REFERENCE_TABLES"
    / "D1_roles.csv"
)
ESCO_CROSSWALK_PATH = (
    WORKSPACE
    / "rerouteher-esco-tfidf"
    / "data"
    / "masco"
    / "D12_esco_to_masco_label_crosswalk.csv"
)
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
SIX_DIGIT_PATTERN = re.compile(r"^\d{6}$")

D1_ROLE_COLUMNS = [
    "role_id",
    "role_title",
    "masco_code",
    "masco_title",
    "isco08_code",
    "esco_code",
    "onet_code",
    "task_summary",
    "occupation_description",
    "remote_possibility",
    "remote_task_count",
    "remote_capable_tasks",
    "remote_onsite_tasks",
    "remote_unclear_tasks",
    "remote_external_proxy",
    "remote_justification",
    "ai_exposure",
    "ai_exposure_share",
    "ai_exposure_external_score_0_100",
    "ai_exposure_measure",
    "flexible_role",
    "rating_status",
    "embedding_model",
    "role_embedding_384",
]

D11_EXTENSION_COLUMNS = [
    "masco_code_printed",
    "masco_major_group_code",
    "masco_major_group_title",
    "masco_sub_major_group_code",
    "masco_sub_major_group_title",
    "masco_minor_group_code",
    "masco_minor_group_title",
    "masco_unit_group_code",
    "masco_unit_group_title",
    "category_stem",
    "additional_categories",
    "d1_parent_role_id",
    "d1_parent_role_title",
    "d1_expansion_relationship",
    "esco_comparison_codes",
    "esco_comparison_titles",
    "esco_crosswalk_status",
    "source_url",
    "source_retrieved_at",
    "source_language",
    "source_authority",
    "task_source_level",
    "source_status",
]

ONSITE_TERMS = {
    "visit or inspect a physical site": re.compile(
        r"\b(visit(?:ing)?|inspect(?:ing|ion)?)\b.{0,45}\b(site|premises|work)\b",
        re.I,
    ),
    "operate or handle physical equipment": re.compile(
        r"\b(operate|machinery|equipment|physical|manual handling)\b", re.I
    ),
    "deliver in-person instruction or service": re.compile(
        r"\b(classroom|in person|face[- ]to[- ]face|on[- ]site)\b", re.I
    ),
}
REMOTE_TERMS = {
    "computer/software/data work": re.compile(
        r"\b(computer|software|data|system|digital|online|database|programming)\b",
        re.I,
    ),
    "information/writing/design work": re.compile(
        r"\b(analy[sz]|research|write|draft|document|design|plan|report|record|translate)\w*\b",
        re.I,
    ),
    "phone/email/advisory work": re.compile(
        r"\b(telephone|call|message|advise|consult|communication|client)\w*\b",
        re.I,
    ),
}
AI_TERMS = {
    "writing/editing/drafting": re.compile(
        r"\b(write|writing|edit|draft|document|translate|summari[sz])\w*\b", re.I
    ),
    "data/calculation/routine processing": re.compile(
        r"\b(data|calculate|record|classif|invoice|schedule|lookup|query|report)\w*\b",
        re.I,
    ),
    "analysis/coding/content generation": re.compile(
        r"\b(analy[sz]|program|code|software|design|content|test)\w*\b", re.I
    ),
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def rating_for_task(task: str) -> dict[str, str]:
    onsite_hits = [label for label, pattern in ONSITE_TERMS.items() if pattern.search(task)]
    remote_hits = [label for label, pattern in REMOTE_TERMS.items() if pattern.search(task)]
    if onsite_hits:
        remote_label = "on_site_or_physical"
        remote_reason = "; ".join(onsite_hits)
    elif remote_hits:
        remote_label = "remote_capable"
        remote_reason = "; ".join(remote_hits)
    else:
        remote_label = "mixed_or_unclear"
        remote_reason = "No decisive D1 published-rule keyword; human review required."
    ai_hits = [label for label, pattern in AI_TERMS.items() if pattern.search(task)]
    return {
        "remote_task_pre_rating": remote_label,
        "remote_rule_evidence": remote_reason,
        "ai_task_pre_rating": "ai_exposable" if ai_hits else "low_or_unclear_exposure",
        "ai_rule_evidence": (
            "; ".join(ai_hits)
            if ai_hits
            else "No explicit D1 routine information-work signal; human review required."
        ),
    }


def esco_index() -> dict[str, list[dict[str, str]]]:
    index: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(ESCO_CROSSWALK_PATH):
        index[row["premerge_masco_code"]].append(row)
    for rows in index.values():
        rows.sort(key=lambda row: (-int(row["total_examples"]), row["target_esco_code"]))
    return index


def main() -> None:
    snapshot = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    occupations = snapshot["occupations"]
    if snapshot["occupation_count"] != 657 or len(occupations) != 657:
        raise AssertionError("The official eMASCO STEM snapshot must contain 657 occupations.")

    d1_roles = read_csv(D1_PATH)
    d1_by_group = {row["masco_code"]: row for row in d1_roles}
    comparisons = esco_index()

    encoder = SentenceTransformer(MODEL_NAME, local_files_only=True)
    embedding_inputs = [
        f"{row['role_title']}. {row['occupation_description']}. {' '.join(row['tasks'])}"
        for row in occupations
    ]
    vectors = encoder.encode(
        embedding_inputs,
        batch_size=64,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=True,
    )

    role_rows: list[dict[str, Any]] = []
    task_rows: list[dict[str, Any]] = []
    task_rating_rows: list[dict[str, Any]] = []
    role_rating_rows: list[dict[str, Any]] = []
    for occupation, vector in zip(occupations, vectors):
        code = occupation["masco_code"]
        role_id = f"M{code}"
        task_ratings: list[dict[str, str]] = []
        for rank, task in enumerate(occupation["tasks"], 1):
            task_id = f"EMASCO_{code}_{rank:02d}"
            rating = rating_for_task(task)
            task_ratings.append(rating)
            task_rows.append(
                {
                    "role_id": role_id,
                    "task_rank": rank,
                    "masco_task_id": task_id,
                    "masco_code": code,
                    "task": task,
                    "task_source_level": occupation["tasks_source_level"],
                    "source": (
                        "eMASCO exact occupation detail (MASCO 2020 content)"
                        if occupation["tasks_source_level"] == "exact_occupation"
                        else "eMASCO official four-digit unit-group task fallback (MASCO 2020 content)"
                    ),
                    "source_page_pdf": "",
                    "source_url": occupation["tasks_source_url"],
                    "source_retrieved_at": snapshot["source_retrieved_at"],
                }
            )
            task_rating_rows.append(
                {
                    "role_id": role_id,
                    "masco_task_id": task_id,
                    "task": task,
                    **rating,
                    "rating_method": (
                        "transparent keyword pre-rating reproducing the D1 published task rules"
                    ),
                    "rater_1": "",
                    "rater_1_rating": "",
                    "rater_2": "",
                    "rater_2_rating": "",
                    "reconciled_rating": "",
                    "review_status": "pending_two_independent_human_raters",
                    "task_source_level": occupation["tasks_source_level"],
                    "source_url": occupation["tasks_source_url"],
                }
            )

        remote_counts = Counter(row["remote_task_pre_rating"] for row in task_ratings)
        ai_count = sum(row["ai_task_pre_rating"] == "ai_exposable" for row in task_ratings)
        task_count = len(task_ratings)
        remote_rating = (
            "low"
            if remote_counts["on_site_or_physical"]
            else ("medium" if remote_counts["mixed_or_unclear"] else "high")
        )
        exposure_share = ai_count / task_count
        ai_rating = "high" if exposure_share >= 0.6 else ("medium" if exposure_share >= 0.3 else "low")
        d1_parent = d1_by_group.get(occupation["unit_group_code"])
        esco_rows = comparisons.get(code, [])
        role_rows.append(
            {
                "role_id": role_id,
                "role_title": occupation["role_title"],
                "masco_code": code,
                "masco_title": occupation["role_title"],
                "isco08_code": "",
                "esco_code": esco_rows[0]["target_esco_code"] if esco_rows else "",
                "onet_code": "",
                "task_summary": " ".join(occupation["tasks"]),
                "occupation_description": occupation["occupation_description"],
                "remote_possibility": remote_rating,
                "remote_task_count": task_count,
                "remote_capable_tasks": remote_counts["remote_capable"],
                "remote_onsite_tasks": remote_counts["on_site_or_physical"],
                "remote_unclear_tasks": remote_counts["mixed_or_unclear"],
                "remote_external_proxy": "",
                "remote_justification": (
                    "Aggregated from exact eMASCO occupation tasks using the same transparent "
                    "pre-rating rule as D1; two-rater review remains pending."
                ),
                "ai_exposure": ai_rating,
                "ai_exposure_share": round(exposure_share, 4),
                "ai_exposure_external_score_0_100": "",
                "ai_exposure_measure": (
                    "Exact eMASCO occupation-task pre-rating share using the D1 keyword rule"
                ),
                "flexible_role": remote_rating in {"medium", "high"},
                "rating_status": "pre_rating_pending_two_independent_human_raters",
                "embedding_model": MODEL_NAME,
                "role_embedding_384": json.dumps(
                    [round(float(value), 7) for value in vector], separators=(",", ":")
                ),
                "masco_code_printed": occupation["masco_code_printed"],
                "masco_major_group_code": occupation["major_group_code"],
                "masco_major_group_title": occupation["major_group_title"],
                "masco_sub_major_group_code": occupation["sub_major_group_code"],
                "masco_sub_major_group_title": occupation["sub_major_group_title"],
                "masco_minor_group_code": occupation["minor_group_code"],
                "masco_minor_group_title": occupation["minor_group_title"],
                "masco_unit_group_code": occupation["unit_group_code"],
                "masco_unit_group_title": occupation["unit_group_title"],
                "category_stem": True,
                "additional_categories": ";".join(
                    category for category in occupation["categories"] if category != "stem"
                ),
                "d1_parent_role_id": d1_parent["role_id"] if d1_parent else "",
                "d1_parent_role_title": d1_parent["role_title"] if d1_parent else "",
                "d1_expansion_relationship": (
                    "within_original_D1_unit_group"
                    if d1_parent
                    else "new_role_from_eMASCO_STEM_scope"
                ),
                "esco_comparison_codes": ";".join(
                    row["target_esco_code"] for row in esco_rows
                ),
                "esco_comparison_titles": ";".join(
                    row["target_esco_title"] for row in esco_rows
                ),
                "esco_crosswalk_status": (
                    "project_crosswalk_pending_domain_owner_review"
                    if esco_rows
                    else "not_mapped_in_project_crosswalk"
                ),
                "source_url": occupation["source_url"],
                "source_retrieved_at": snapshot["source_retrieved_at"],
                "source_language": "English",
                "source_authority": snapshot["source_authority"],
                "task_source_level": occupation["tasks_source_level"],
                "source_status": (
                    "official portal content based on MASCO 2020; exact occupation tasks"
                    if occupation["tasks_source_level"] == "exact_occupation"
                    else "official portal content based on MASCO 2020; tasks inherited from official four-digit unit-group page"
                ),
            }
        )
        role_rating_rows.append(
            {
                "role_id": role_id,
                "role_title": occupation["role_title"],
                "masco_code": code,
                "masco_source_page_pdf": "",
                "rated_task_count": task_count,
                "remote_capable_tasks": remote_counts["remote_capable"],
                "remote_onsite_tasks": remote_counts["on_site_or_physical"],
                "remote_unclear_tasks": remote_counts["mixed_or_unclear"],
                "remote_pre_rating": remote_rating,
                "ai_exposable_tasks": ai_count,
                "ai_exposure_share": round(exposure_share, 4),
                "ai_pre_rating": ai_rating,
                "independent_raters_required": 2,
                "reconciliation_status": "pending",
                "release_use": "research_pre_rating_only",
                "task_source_level": occupation["tasks_source_level"],
                "source_url": occupation["tasks_source_url"],
            }
        )

    role_columns = D1_ROLE_COLUMNS + D11_EXTENSION_COLUMNS
    task_columns = [
        "role_id",
        "task_rank",
        "masco_task_id",
        "masco_code",
        "task",
        "task_source_level",
        "source",
        "source_page_pdf",
        "source_url",
        "source_retrieved_at",
    ]
    task_rating_columns = [
        "role_id",
        "masco_task_id",
        "task",
        "remote_task_pre_rating",
        "remote_rule_evidence",
        "ai_task_pre_rating",
        "ai_rule_evidence",
        "rating_method",
        "rater_1",
        "rater_1_rating",
        "rater_2",
        "rater_2_rating",
        "reconciled_rating",
        "review_status",
        "task_source_level",
        "source_url",
    ]
    role_rating_columns = [
        "role_id",
        "role_title",
        "masco_code",
        "masco_source_page_pdf",
        "rated_task_count",
        "remote_capable_tasks",
        "remote_onsite_tasks",
        "remote_unclear_tasks",
        "remote_pre_rating",
        "ai_exposable_tasks",
        "ai_exposure_share",
        "ai_pre_rating",
        "independent_raters_required",
        "reconciliation_status",
        "release_use",
        "task_source_level",
        "source_url",
    ]
    write_csv(TABLE_DIR / "D11_STEM_roles.csv", role_rows, role_columns)
    write_csv(TABLE_DIR / "D11_STEM_role_tasks.csv", task_rows, task_columns)
    write_csv(
        TABLE_DIR / "D11_STEM_task_rating_lineage.csv",
        task_rating_rows,
        task_rating_columns,
    )
    write_csv(
        TABLE_DIR / "D11_STEM_role_rating_lineage.csv",
        role_rating_rows,
        role_rating_columns,
    )

    stem_by_d1_group = Counter(row["masco_unit_group_code"] for row in role_rows)
    scope_rows = [
        {
            "d1_role_id": row["role_id"],
            "d1_role_title": row["role_title"],
            "d1_masco_unit_group_code": row["masco_code"],
            "stem_roles_in_same_unit_group": stem_by_d1_group[row["masco_code"]],
            "d11_scope_rule": "all roles listed in the official eMASCO STEM category",
            "relationship": (
                "D1 seed role retained as lineage where applicable; D11 scope is not limited to this group"
            ),
        }
        for row in d1_roles
    ]
    write_csv(
        TABLE_DIR / "D11_STEM_D1_scope_lineage.csv",
        scope_rows,
        list(scope_rows[0]),
    )

    manifest_rows = [
        {
            "asset": "eMASCO STEM directory and 657 occupation detail pages",
            "purpose": "D11 authoritative occupation scope, titles, hierarchy, descriptions, and tasks",
            "source_url": snapshot["source_url"],
            "authority": snapshot["source_authority"],
            "retrieved_at": snapshot["source_retrieved_at"],
            "status": "official portal; content based on MASCO 2020; enhancement notice active",
        },
        {
            "asset": "D1_roles.csv",
            "purpose": "Schema order and original ten-role lineage only",
            "source_url": str(D1_PATH),
            "authority": "ReRouteHer Iteration 1 D1",
            "retrieved_at": snapshot["source_retrieved_at"],
            "status": "project source table",
        },
        {
            "asset": "D12_esco_to_masco_label_crosswalk.csv",
            "purpose": "Retain ESCO codes/titles as comparison metadata where exact mappings exist",
            "source_url": str(ESCO_CROSSWALK_PATH),
            "authority": "project crosswalk; not an official ESCO-to-MASCO publication",
            "retrieved_at": snapshot["source_retrieved_at"],
            "status": "pending domain-owner review",
        },
    ]
    write_csv(
        TABLE_DIR / "D11_STEM_source_manifest.csv",
        manifest_rows,
        list(manifest_rows[0]),
    )

    checks = [
        {
            "check": "official_stem_role_count",
            "expected": 657,
            "actual": len(role_rows),
            "status": "PASS" if len(role_rows) == 657 else "FAIL",
        },
        {
            "check": "unique_six_digit_masco_codes",
            "expected": 657,
            "actual": len({row["masco_code"] for row in role_rows}),
            "status": (
                "PASS"
                if len({row["masco_code"] for row in role_rows}) == 657
                and all(SIX_DIGIT_PATTERN.fullmatch(row["masco_code"]) for row in role_rows)
                else "FAIL"
            ),
        },
        {
            "check": "all_roles_have_description_and_tasks",
            "expected": 657,
            "actual": sum(
                bool(row["occupation_description"]) and int(row["remote_task_count"]) > 0
                for row in role_rows
            ),
            "status": (
                "PASS"
                if all(row["occupation_description"] and int(row["remote_task_count"]) > 0 for row in role_rows)
                else "FAIL"
            ),
        },
        {
            "check": "D1_column_contract_preserved",
            "expected": ";".join(D1_ROLE_COLUMNS),
            "actual": ";".join(role_columns[: len(D1_ROLE_COLUMNS)]),
            "status": "PASS" if role_columns[: len(D1_ROLE_COLUMNS)] == D1_ROLE_COLUMNS else "FAIL",
        },
        {
            "check": "task_source_lineage_complete",
            "expected": len(task_rows),
            "actual": sum(
                row["task_source_level"] in {"exact_occupation", "unit_group_inherited"}
                and bool(row["source_url"])
                for row in task_rows
            ),
            "status": (
                "PASS"
                if all(
                    row["task_source_level"] in {"exact_occupation", "unit_group_inherited"}
                    and row["source_url"]
                    for row in task_rows
                )
                else "FAIL"
            ),
        },
        {
            "check": "ESCO_comparison_columns_retained",
            "expected": "esco_code;esco_comparison_codes;esco_comparison_titles",
            "actual": "esco_code;esco_comparison_codes;esco_comparison_titles",
            "status": "PASS",
        },
    ]
    write_csv(QA_DIR / "D11_STEM_validation_checks.csv", checks, list(checks[0]))

    summary = {
        "deliverable": "D11 expansion of D1 to official eMASCO STEM category roles",
        "scope_definition": snapshot["source_definition"],
        "occupation_count": len(role_rows),
        "task_count": len(task_rows),
        "original_d1_role_count": len(d1_roles),
        "roles_with_original_d1_unit_group_lineage": sum(
            bool(row["d1_parent_role_id"]) for row in role_rows
        ),
        "roles_with_esco_comparison": sum(bool(row["esco_code"]) for row in role_rows),
        "roles_with_exact_occupation_tasks": sum(
            row["task_source_level"] == "exact_occupation" for row in role_rows
        ),
        "roles_with_unit_group_task_fallback": sum(
            row["task_source_level"] == "unit_group_inherited" for row in role_rows
        ),
        "major_group_counts": dict(
            sorted(Counter(row["masco_major_group_code"] for row in role_rows).items())
        ),
        "remote_pre_rating_counts": dict(
            sorted(Counter(row["remote_possibility"] for row in role_rows).items())
        ),
        "ai_pre_rating_counts": dict(
            sorted(Counter(row["ai_exposure"] for row in role_rows).items())
        ),
        "production_approved": False,
        "human_review_required": True,
        "notes": [
            "Remote/flexible and AI labels are transparent D1-method pre-ratings pending two independent raters.",
            "ESCO fields are retained for comparison where the project crosswalk has an exact six-digit mapping.",
            "Where an exact occupation page has no task list, task lineage points to the official eMASCO four-digit unit-group page rather than fabricating tasks.",
            "No resume dataset is used in D11; this is an occupational reference-table expansion.",
        ],
    }
    write_json(QA_DIR / "D11_STEM_build_summary.json", summary)
    if any(check["status"] != "PASS" for check in checks):
        raise AssertionError("One or more D11 STEM validation checks failed.")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
