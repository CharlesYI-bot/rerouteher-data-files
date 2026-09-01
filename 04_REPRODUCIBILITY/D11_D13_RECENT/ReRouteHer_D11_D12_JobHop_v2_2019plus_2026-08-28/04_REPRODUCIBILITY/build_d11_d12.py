from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = PACKAGE_ROOT.parent
sys.path.insert(0, str(WORKSPACE / ".work" / "fastembed"))
sys.path.insert(0, str(WORKSPACE / ".work" / "sklearn"))

import joblib  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import sklearn  # noqa: E402
from fastembed import TextEmbedding  # noqa: E402
from pypdf import PdfReader  # noqa: E402
from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import (  # noqa: E402
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    top_k_accuracy_score,
)
from sklearn.pipeline import FeatureUnion, Pipeline  # noqa: E402


SOURCE_RELEASE = WORKSPACE / "ReRouteHer_TeamDrive_Upload_2026-08-27"
SOURCE_DATA = SOURCE_RELEASE / "02_RAW_SOURCE_DATA"
SOURCE_PROCESSED = SOURCE_RELEASE / "03_PROCESSED_DATA"
SOURCE_REFERENCE = SOURCE_PROCESSED / "01_REFERENCE_TABLES"
SOURCE_D9 = SOURCE_PROCESSED / "02_RESUME_MODEL"
SOURCE_OCCUPATIONS = SOURCE_PROCESSED / "04_ESCO_OCCUPATION_MODEL"
EMBEDDING_CACHE = (
    WORKSPACE
    / "ReRouteHer_DataTeam_Fresh_HighStandard_2026-08-27"
    / "00_SOURCE_ARCHIVE"
    / "EMBEDDING_MODEL_CACHE"
)

D11_DIR = PACKAGE_ROOT / "01_D11_REFERENCE_TABLES"
D12_DIR = PACKAGE_ROOT / "02_D12_MODEL"
DATABASE_DIR = PACKAGE_ROOT / "03_DATABASE"
QA_DIR = PACKAGE_ROOT / "05_QA"
for directory in (D11_DIR, D12_DIR, DATABASE_DIR, QA_DIR):
    directory.mkdir(parents=True, exist_ok=True)

JOBHOP_PATH = (
    SOURCE_DATA / "RESUME_APPROVED" / "jobhop_v2_confirmed_active_2019plus.csv"
)
JOBHOP_AUDIT_PATH = (
    SOURCE_DATA
    / "RESUME_APPROVED"
    / "jobhop_v2_confirmed_active_2019plus_audit.json"
)
MASCO_PDF_PATH = SOURCE_DATA / "MASCO_2020_English_official.pdf"
ESCO_ONET_PATH = SOURCE_DATA / "ESCO_to_ONET-SOC_official.xlsx"
D1_ROLES_PATH = SOURCE_REFERENCE / "D1_roles.csv"
ESCO_PROFILES_PATH = SOURCE_OCCUPATIONS / "esco_occupation_profiles.csv"
D9_METRICS_PATH = SOURCE_D9 / "D9_metrics.json"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
LABEL_PATTERN = r"^\d{6}$"
MIN_TRAIN_SUPPORT = 5
RANDOM_STATE = 42

# Each tuple is:
# role_id, current curated role, MASCO parent group, exact six-digit MASCO anchor,
# JobHop/ESCO target group. The parent group is extraction lineage only; it is
# never used as a D11 role code or D12 prediction label.
ROLE_SPECS = [
    ("R01", "Software Developer", "2512", "251201", "2512"),
    ("R02", "Data Analyst", "2524", "252403", "2511"),
    ("R03", "Human Resources Officer", "2423", "242323", "2423"),
    ("R04", "Online Marketing Specialist", "2431", "243135", "2431"),
    ("R05", "Translator", "2833", "283302", "2643"),
    ("R06", "Graphic Designer", "2543", "254302", "2166"),
    ("R07", "Accounting & Bookkeeping Clerk", "4311", "431105", "4311"),
    ("R08", "Customer Contact Centre Officer", "4222", "422207", "4222"),
    ("R09", "Secretary / Administrative Assistant", "4121", "412107", "4120"),
    ("R10", "Tutor", "2311", "231109", "2359"),
]

ROLE_BY_ID = {row[0]: row for row in ROLE_SPECS}
ROLE_BY_TARGET_GROUP = {row[4]: row[0] for row in ROLE_SPECS}
ANCHOR_BY_ROLE = {row[0]: row[3] for row in ROLE_SPECS}
PARENT_BY_ROLE = {row[0]: row[2] for row in ROLE_SPECS}

# Curated ESCO-title -> MASCO six-digit crosswalk. These are the only JobHop
# target labels present in the approved 2019+ transition sample. Entries remain
# traceable in D12_esco_to_masco_label_crosswalk.csv and are not asserted as an
# official ESCO-to-MASCO crosswalk.
TARGET_TO_MASCO = {
    "2512.4": "251201",
    "2512.5": "251206",
    "2512.1": "251245",
    "2511.10": "252416",
    "2511.16": "252418",
    "2511.13": "252403",
    "2511.3": "252403",
    "2511.6": "252406",
    "2511.12": "252403",
    "2511.15": "252418",
    "2511.19": "252403",
    "2511.2": "252411",
    "2511.4": "252401",
    "2511.9": "252416",
    "2423.6": "242321",
    "2423.3": "242323",
    "2423.2": "242307",
    "2423.4": "242310",
    "2423.1": "242309",
    "2423.5": "242305",
    "2431.10.4": "243135",
    "2431.10.3": "243136",
    "2431.6": "243121",
    "2431.5": "243121",
    "2431.10": "243110",
    "2431.13": "243135",
    "2431.16": "243103",
    "2431.4": "243123",
    "2431.1": "243101",
    "2431.11": "243107",
    "2431.15": "243114",
    "2431.14": "243108",
    "2431.7": "243101",
    "2431.10.2": "243121",
    "2431.3": "243101",
    "2643.2": "283303",
    "2643.6": "283302",
    "2643.4.1": "283304",
    "2643.5": "283306",
    "2643.4": "283304",
    "2643.6.1": "283302",
    "2643.6.2": "283307",
    "2166.9": "254302",
    "2166.14": "254309",
    "2166.7": "254316",
    "2166.4": "254306",
    "2166.1": "254307",
    "2166.3": "254309",
    "2166.5": "254316",
    "2166.10": "254308",
    "2166.11": "254308",
    "2166.12": "254308",
    "2166.2": "254309",
    "2166.6": "254316",
    "4311.2": "431110",
    "4311.1": "431118",
    "4222.1": "422207",
    "4120.1": "412107",
    "2359.11": "231109",
    "2359.14": "231109",
    "2359.7": "231109",
    "2359.1": "231109",
    "2359.2": "231109",
    "2359.9": "231109",
    "2359.4": "231109",
    "2359.10": "231109",
    "2359.5": "231109",
    "2359.8": "231109",
    "2359.3": "231109",
    "2359.6": "231109",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def clean(value: Any) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\u00ad", " ")).strip()


def nullable(value: Any) -> Any:
    text = clean(value)
    return text if text else None


def vector_json(vector: np.ndarray) -> str:
    return json.dumps(
        [round(float(value), 7) for value in vector], separators=(",", ":")
    )


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def sql_literal(value: Any) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "NULL"
    if isinstance(value, (bool, np.bool_)):
        return "TRUE" if bool(value) else "FALSE"
    if isinstance(value, (int, float, np.integer, np.floating)):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


def parse_masco_granular_index() -> tuple[pd.DataFrame, dict[str, str]]:
    reader = PdfReader(str(MASCO_PDF_PATH))
    selected_groups = {row[2] for row in ROLE_SPECS}
    records: dict[str, dict[str, Any]] = {}
    parent_titles: dict[str, str] = {}

    for page_number, page in enumerate(reader.pages, 1):
        text = (page.extract_text() or "").replace("\u00ad", "")
        if 317 <= page_number <= 444:
            for line in text.splitlines():
                match = re.match(r"^\s*(\d{4})-(\d{2})\s+(.*)$", line)
                if not match or match.group(1) not in selected_groups:
                    continue
                parent, suffix, raw_title = match.groups()
                title = re.sub(
                    r"^(?:\d{4}-\d{2}|New)\s+", "", clean(raw_title), flags=re.I
                )
                six_digit = parent + suffix
                existing = records.get(six_digit)
                if existing and existing["role_title"] != title:
                    raise AssertionError(
                        f"Conflicting MASCO titles for {six_digit}: "
                        f"{existing['role_title']!r} versus {title!r}"
                    )
                records[six_digit] = {
                    "masco_code": six_digit,
                    "masco_code_printed": f"{parent}-{suffix}",
                    "source_parent_group_code": parent,
                    "role_title": title,
                    "source_page_granular_index": page_number,
                }

        unit_match = re.search(r"UNIT\s+GROUP\s+(\d{4})\s+([^\n]+)", text, re.I)
        if unit_match and unit_match.group(1) in selected_groups:
            parent_titles.setdefault(
                unit_match.group(1), clean(unit_match.group(2)).title()
            )

    frame = pd.DataFrame(records.values()).sort_values("masco_code").reset_index(drop=True)
    if frame.empty:
        raise AssertionError("No granular MASCO rows parsed")
    if not frame["masco_code"].str.fullmatch(LABEL_PATTERN).all():
        raise AssertionError("Every D11 MASCO role code must be exactly six digits")
    if frame["masco_code"].duplicated().any():
        raise AssertionError("Duplicate six-digit MASCO codes parsed")
    missing_groups = selected_groups - set(frame["source_parent_group_code"])
    if missing_groups:
        raise AssertionError(f"MASCO groups missing from granular index: {missing_groups}")
    for role_id, _, parent, anchor, _ in ROLE_SPECS:
        if anchor not in set(frame["masco_code"]):
            raise AssertionError(f"Anchor {anchor} for {role_id} not found in MASCO PDF")
        group_codes = frame.loc[
            frame["source_parent_group_code"].eq(parent), "masco_code"
        ]
        suffixes = sorted(int(code[-2:]) for code in group_codes)
        if suffixes != list(range(1, max(suffixes) + 1)):
            raise AssertionError(f"Non-contiguous granular MASCO codes in group {parent}")
    return frame, parent_titles


def build_d11(embedder: TextEmbedding) -> tuple[pd.DataFrame, dict[str, Any]]:
    granular, parent_titles = parse_masco_granular_index()
    parent_roles = pd.read_csv(D1_ROLES_PATH, dtype=str, keep_default_na=False)
    parent_by_role = parent_roles.set_index("role_id").to_dict("index")
    role_id_by_parent = {row[2]: row[0] for row in ROLE_SPECS}
    anchor_role_by_code = {row[3]: row[0] for row in ROLE_SPECS}

    rows: list[dict[str, Any]] = []
    for item in granular.to_dict("records"):
        parent_code = item["source_parent_group_code"]
        source_role_id = role_id_by_parent[parent_code]
        source = parent_by_role[source_role_id]
        is_anchor = item["masco_code"] in anchor_role_by_code
        role_id = anchor_role_by_code.get(item["masco_code"], f"M{item['masco_code']}")
        task_summary = clean(source["task_summary"])
        occupation_description = clean(source["occupation_description"])
        rows.append(
            {
                "role_id": role_id,
                "role_title": item["role_title"],
                "masco_code": item["masco_code"],
                "masco_code_printed": item["masco_code_printed"],
                "masco_title": item["role_title"],
                "source_parent_group_code": parent_code,
                "source_parent_role_id": source_role_id,
                "source_parent_title": parent_titles.get(
                    parent_code, clean(source.get("masco_title"))
                ),
                "isco08_code": nullable(source.get("isco08_code")) if is_anchor else None,
                "esco_code": nullable(source.get("esco_code")) if is_anchor else None,
                "onet_code": nullable(source.get("onet_code")) if is_anchor else None,
                "task_summary": task_summary,
                "occupation_description": occupation_description,
                "remote_possibility": nullable(source.get("remote_possibility")),
                "remote_task_count": nullable(source.get("remote_task_count")),
                "remote_capable_tasks": nullable(source.get("remote_capable_tasks")),
                "remote_onsite_tasks": nullable(source.get("remote_onsite_tasks")),
                "remote_unclear_tasks": nullable(source.get("remote_unclear_tasks")),
                "remote_external_proxy": nullable(source.get("remote_external_proxy")),
                "remote_justification": (
                    "Inherited from the MASCO four-digit unit-group task rating; "
                    "child-specific human review remains pending."
                ),
                "ai_exposure": nullable(source.get("ai_exposure")),
                "ai_exposure_share": nullable(source.get("ai_exposure_share")),
                "ai_exposure_external_score_0_100": nullable(
                    source.get("ai_exposure_external_score_0_100")
                ),
                "ai_exposure_measure": (
                    "Inherited from the D1 MASCO unit-group task pre-rating."
                ),
                "flexible_role": bool(is_anchor),
                "rating_status": (
                    "unit_group_inherited_pending_child_specific_two_rater_review"
                ),
                "rating_method": (
                    "D11 unit-group inheritance permitted by task brief; exact anchor "
                    "occupations retain flexible_role=true."
                ),
                "source_page_granular_index": item["source_page_granular_index"],
                "embedding_model": MODEL_NAME,
            }
        )

    d11 = pd.DataFrame(rows).sort_values("masco_code").reset_index(drop=True)
    texts = (
        d11["role_title"].fillna("")
        + ". "
        + d11["occupation_description"].fillna("")
        + ". "
        + d11["task_summary"].fillna("")
    ).tolist()
    vectors = np.asarray(list(embedder.embed(texts, batch_size=32)))
    if vectors.shape != (len(d11), 384):
        raise AssertionError(f"Unexpected D11 embedding shape {vectors.shape}")
    d11["role_embedding_384"] = [vector_json(vector) for vector in vectors]

    d11.to_csv(D11_DIR / "D11_masco_granular_roles.csv", index=False)
    anchor_rows = []
    for role_id, curated_title, parent, anchor, target_group in ROLE_SPECS:
        match = d11[d11["masco_code"].eq(anchor)].iloc[0]
        anchor_rows.append(
            {
                "role_id": role_id,
                "curated_role_title": curated_title,
                "d11_masco_code": anchor,
                "d11_masco_code_printed": match["masco_code_printed"],
                "d11_masco_title": match["role_title"],
                "source_parent_group_code": parent,
                "jobhop_esco_target_group": target_group,
                "anchor_method": "curated exact or closest MASCO 2020 granular occupation",
                "review_status": "requires domain-owner confirmation before production",
            }
        )
    pd.DataFrame(anchor_rows).to_csv(
        D11_DIR / "D11_curated_role_anchor_map.csv", index=False
    )

    lineage = d11[
        [
            "masco_code",
            "masco_code_printed",
            "role_title",
            "source_parent_group_code",
            "source_parent_role_id",
            "source_page_granular_index",
            "rating_method",
        ]
    ].copy()
    lineage["source"] = "MASCO 2020 official PDF"
    lineage["task_text_source"] = "D1 MASCO unit-group task section"
    lineage["embedding_text"] = "role_title + occupation_description + task_summary"
    lineage.to_csv(D11_DIR / "D11_masco_granular_lineage.csv", index=False)

    group_counts = (
        d11.groupby("source_parent_group_code").size().sort_index().astype(int).to_dict()
    )
    audit = {
        "task": "D11",
        "source": str(MASCO_PDF_PATH.relative_to(WORKSPACE)),
        "source_sha256": sha256(MASCO_PDF_PATH),
        "role_code_rule": "exactly six digits; printed MASCO hyphen retained separately",
        "role_code_regex": LABEL_PATTERN,
        "granular_roles": len(d11),
        "unique_masco_codes": int(d11["masco_code"].nunique()),
        "parent_groups": group_counts,
        "curated_anchor_roles": int(d11["flexible_role"].sum()),
        "rating_method": "inherit D1 unit-group rating; child-specific two-rater review pending",
        "embedding_model": MODEL_NAME,
        "embedding_shape": list(vectors.shape),
        "all_codes_six_digit": bool(d11["masco_code"].str.fullmatch(LABEL_PATTERN).all()),
        "four_digit_role_codes": int(d11["masco_code"].str.len().eq(4).sum()),
    }
    write_json(D11_DIR / "D11_extraction_audit.json", audit)
    build_migration_sql(d11)
    return d11, audit


def parse_quarter(value: str) -> int:
    match = re.fullmatch(r"\s*Q([1-4])\s+((?:19|20)\d{2})\s*", str(value))
    if not match:
        raise ValueError(f"Invalid JobHop quarter-year value: {value!r}")
    quarter, year = map(int, match.groups())
    return year * 4 + quarter - 1


def compose_record_text(
    row: pd.Series,
    title_map: dict[str, str],
    skill_map: dict[str, str],
) -> str:
    code = str(row["matched_code"])
    title = clean(title_map.get(code, code)).lower()
    skills = [
        clean(value).lower()
        for value in str(skill_map.get(code, "")).split("|")[:3]
        if clean(value)
    ]
    duration_quarters = max(
        1, parse_quarter(row["end_date"]) - parse_quarter(row["start_date"]) + 1
    )
    duration_years = duration_quarters / 4
    parts = [f"title {title}"]
    if skills:
        parts.append("skills " + ", ".join(skills))
    parts.append(f"duration {duration_years:.2f} years")
    return " ; ".join(parts)


def build_jobhop_examples(d11: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    source = pd.read_csv(
        JOBHOP_PATH,
        dtype={"resume_id": str, "matched_code": str, "split": str},
        keep_default_na=False,
    )
    source["target_group"] = source["matched_code"].str.extract(r"^(\d{4})")
    source["end_index"] = source["end_date"].map(parse_quarter)
    source["start_index"] = source["start_date"].map(parse_quarter)

    crosswalk = pd.read_excel(ESCO_ONET_PATH, header=3, dtype=str)
    title_map = (
        crosswalk[["ESCO/ISCO Code", "ESCO/ISCO Title"]]
        .dropna()
        .drop_duplicates("ESCO/ISCO Code")
        .set_index("ESCO/ISCO Code")["ESCO/ISCO Title"]
        .map(clean)
        .to_dict()
    )
    profiles = pd.read_csv(ESCO_PROFILES_PATH, dtype=str, keep_default_na=False)
    title_map.update(
        profiles.drop_duplicates("esco_code").set_index("esco_code")["esco_title"].to_dict()
    )
    skill_map = (
        profiles.drop_duplicates("esco_code")
        .set_index("esco_code")["top_skill_groups"]
        .to_dict()
    )

    # Preserve the established D9 target-selection contract exactly. Quarter
    # values remain available for duration features, but D9 selected the latest
    # target by end year, start year and code. Changing this ordering here would
    # silently redefine which job is the supervised target for same-year rows.
    source = source.sort_values(
        ["resume_id", "end_year", "start_year", "matched_code"], kind="mergesort"
    ).copy()
    raw_examples: list[dict[str, Any]] = []
    split_conflicts = 0
    for resume_id, trajectory in source.groupby("resume_id", sort=False):
        if len(trajectory) < 2:
            continue
        latest = trajectory.iloc[-1]
        role_id = ROLE_BY_TARGET_GROUP.get(str(latest["target_group"]))
        if role_id is None:
            continue
        target_esco_code = str(latest["matched_code"])
        if target_esco_code not in TARGET_TO_MASCO:
            raise AssertionError(
                f"Approved JobHop target lacks curated granular crosswalk: {target_esco_code}"
            )
        split_values = trajectory["split"].dropna().unique().tolist()
        if len(split_values) > 1:
            split_conflicts += 1
        split = split_values[0] if len(split_values) == 1 else str(latest["split"])
        earlier = trajectory.iloc[:-1]
        history = [compose_record_text(row, title_map, skill_map) for _, row in earlier.iterrows()]
        education = clean(latest.get("university_level"))
        text = " || ".join(history)
        if education:
            text += f" || education {education.lower()}"
        raw_examples.append(
            {
                "resume_id": resume_id,
                "split": split,
                "source_parent_role_id": role_id,
                "target_esco_code": target_esco_code,
                "target_esco_title": clean(title_map.get(target_esco_code, target_esco_code)),
                "premerge_masco_code": TARGET_TO_MASCO[target_esco_code],
                "previous_esco_codes": ";".join(earlier["matched_code"].astype(str)),
                "text": text,
                "compose_text_format": (
                    "prior ESCO title + top three ESCO skill groups + duration; "
                    "latest education; latest target excluded"
                ),
            }
        )
    examples = pd.DataFrame(raw_examples)
    if examples.empty:
        raise AssertionError("No D12 JobHop transition examples built")

    d11_codes = set(d11["masco_code"])
    if not set(examples["premerge_masco_code"]).issubset(d11_codes):
        raise AssertionError("D12 premerge crosswalk contains labels absent from D11")
    train_support = (
        examples[examples["split"].eq("train")]["premerge_masco_code"]
        .value_counts()
        .to_dict()
    )
    examples["masco_code"] = examples.apply(
        lambda row: (
            row["premerge_masco_code"]
            if train_support.get(row["premerge_masco_code"], 0) >= MIN_TRAIN_SUPPORT
            else ANCHOR_BY_ROLE[row["source_parent_role_id"]]
        ),
        axis=1,
    )
    examples["sparsity_action"] = np.where(
        examples["masco_code"].eq(examples["premerge_masco_code"]),
        "retained_granular_class",
        "merged_to_six_digit_curated_anchor",
    )
    examples["masco_role_title"] = examples["masco_code"].map(
        d11.set_index("masco_code")["role_title"]
    )
    if not examples["masco_code"].str.fullmatch(LABEL_PATTERN).all():
        raise AssertionError("D12 training labels must be exactly six digits")

    distinct = (
        examples.groupby(
            [
                "source_parent_role_id",
                "target_esco_code",
                "target_esco_title",
                "premerge_masco_code",
                "masco_code",
                "sparsity_action",
            ]
        )
        .agg(
            total_examples=("resume_id", "size"),
            train_examples=("split", lambda values: int((values == "train").sum())),
            val_examples=("split", lambda values: int((values == "val").sum())),
            test_examples=("split", lambda values: int((values == "test").sum())),
        )
        .reset_index()
    )
    title_by_code = d11.set_index("masco_code")["role_title"].to_dict()
    printed_by_code = d11.set_index("masco_code")["masco_code_printed"].to_dict()
    distinct["premerge_masco_title"] = distinct["premerge_masco_code"].map(title_by_code)
    distinct["model_masco_title"] = distinct["masco_code"].map(title_by_code)
    distinct["model_masco_code_printed"] = distinct["masco_code"].map(printed_by_code)
    distinct["crosswalk_method"] = "curated semantic ESCO-title to MASCO 2020 granular title"
    distinct["crosswalk_authority"] = (
        "project crosswalk; not an official ESCO-to-MASCO publication"
    )
    distinct["review_status"] = "pending domain-owner review"
    distinct.to_csv(D12_DIR / "D12_esco_to_masco_label_crosswalk.csv", index=False)

    examples = examples[
        [
            "resume_id",
            "split",
            "masco_code",
            "masco_role_title",
            "premerge_masco_code",
            "sparsity_action",
            "source_parent_role_id",
            "target_esco_code",
            "target_esco_title",
            "previous_esco_codes",
            "text",
            "compose_text_format",
        ]
    ].sort_values(["split", "resume_id"], kind="mergesort")
    examples.to_csv(D12_DIR / "D12_training_examples_jobhop_v2_2019plus.csv", index=False)

    profile = {
        "jobhop_source": str(JOBHOP_PATH.relative_to(WORKSPACE)),
        "jobhop_source_sha256": sha256(JOBHOP_PATH),
        "jobhop_audit_sha256": sha256(JOBHOP_AUDIT_PATH),
        "resume_dataset_policy": "JobHop v2 confirmed-active 2019+ is the sole resume/career-history dataset.",
        "non_resume_reference_sources": [
            "MASCO 2020 official PDF for six-digit target codes/titles/tasks",
            "ESCO official occupation titles/skill groups for feature interpretation",
        ],
        "examples": len(examples),
        "unique_resumes": int(examples["resume_id"].nunique()),
        "split_counts": examples["split"].value_counts().sort_index().astype(int).to_dict(),
        "split_conflict_trajectories": split_conflicts,
        "premerge_classes": int(examples["premerge_masco_code"].nunique()),
        "model_classes": int(examples["masco_code"].nunique()),
        "sparsity_merged_examples": int(
            examples["sparsity_action"].eq("merged_to_six_digit_curated_anchor").sum()
        ),
        "minimum_train_support": MIN_TRAIN_SUPPORT,
        "raw_resume_text_available": False,
        "feature_scope": "structured prior career history; no raw CV text",
    }
    write_json(D12_DIR / "D12_dataset_profile.json", profile)
    return examples, distinct, profile


def evaluate_classifier(
    pipeline: Pipeline, frame: pd.DataFrame, split: str
) -> tuple[dict[str, Any], pd.DataFrame, np.ndarray]:
    truth = frame["masco_code"].astype(str)
    predicted = pipeline.predict(frame["text"].fillna(""))
    probabilities = pipeline.predict_proba(frame["text"].fillna(""))
    classes = list(pipeline.named_steps["classifier"].classes_)
    top_k = min(3, len(classes))
    top_indexes = probabilities.argsort(axis=1)[:, -top_k:][:, ::-1]
    top_codes = [[classes[index] for index in indexes] for indexes in top_indexes]
    report = classification_report(
        truth, predicted, labels=classes, output_dict=True, zero_division=0
    )
    metrics = {
        "split": split,
        "n_examples": len(frame),
        "accuracy": float(accuracy_score(truth, predicted)),
        "macro_f1": float(
            f1_score(truth, predicted, labels=classes, average="macro", zero_division=0)
        ),
        "top3_accuracy": float(
            top_k_accuracy_score(truth, probabilities, k=top_k, labels=classes)
        ),
        "per_class": {
            code: {
                "precision": float(report[code]["precision"]),
                "recall": float(report[code]["recall"]),
                "f1": float(report[code]["f1-score"]),
                "support": int(report[code]["support"]),
            }
            for code in classes
        },
    }
    rows = frame[
        ["resume_id", "masco_code", "premerge_masco_code", "target_esco_code"]
    ].copy()
    rows = rows.rename(columns={"masco_code": "true_masco_code"})
    rows["classifier_masco_code"] = predicted
    rows["classifier_probability"] = probabilities.max(axis=1).round(6)
    rows["top3_masco_codes"] = [";".join(values) for values in top_codes]
    rows["classifier_correct"] = rows["true_masco_code"].eq(
        rows["classifier_masco_code"]
    )
    return metrics, rows, probabilities


def simple_metrics(y_true: list[str], y_pred: list[str], classes: list[str]) -> dict[str, Any]:
    report = classification_report(
        y_true, y_pred, labels=classes, output_dict=True, zero_division=0
    )
    return {
        "n_examples": len(y_true),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(
            f1_score(y_true, y_pred, labels=classes, average="macro", zero_division=0)
        ),
        "per_class": {
            code: {
                "precision": float(report[code]["precision"]),
                "recall": float(report[code]["recall"]),
                "f1": float(report[code]["f1-score"]),
                "support": int(report[code]["support"]),
            }
            for code in classes
        },
    }


def build_d12(
    d11: pd.DataFrame,
    examples: pd.DataFrame,
    profile: dict[str, Any],
    embedder: TextEmbedding,
) -> dict[str, Any]:
    train = examples[examples["split"].eq("train")].copy()
    validation = examples[examples["split"].eq("val")].copy()
    test = examples[examples["split"].eq("test")].copy()

    grid_results = []
    best: tuple[tuple[float, float], float, Pipeline, dict[str, Any]] | None = None
    for c_value in (0.5, 1.0, 2.0, 4.0):
        features = FeatureUnion(
            [
                (
                    "word",
                    TfidfVectorizer(
                        lowercase=True,
                        strip_accents="unicode",
                        analyzer="word",
                        ngram_range=(1, 2),
                        min_df=2,
                        max_df=0.95,
                        sublinear_tf=True,
                        max_features=40000,
                    ),
                ),
                (
                    "character",
                    TfidfVectorizer(
                        lowercase=True,
                        strip_accents="unicode",
                        analyzer="char_wb",
                        ngram_range=(3, 5),
                        min_df=2,
                        max_df=0.98,
                        sublinear_tf=True,
                        max_features=60000,
                    ),
                ),
            ]
        )
        pipeline = Pipeline(
            [
                ("features", features),
                (
                    "classifier",
                    LogisticRegression(
                        C=c_value,
                        class_weight="balanced",
                        max_iter=4000,
                        solver="lbfgs",
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        )
        pipeline.fit(train["text"].fillna(""), train["masco_code"])
        validation_metrics, _, _ = evaluate_classifier(pipeline, validation, "val")
        grid_results.append(
            {
                "C": c_value,
                "validation_accuracy": validation_metrics["accuracy"],
                "validation_macro_f1": validation_metrics["macro_f1"],
                "validation_top3_accuracy": validation_metrics["top3_accuracy"],
            }
        )
        key = (validation_metrics["macro_f1"], validation_metrics["accuracy"])
        if best is None or key > best[0]:
            best = (key, c_value, pipeline, validation_metrics)
    assert best is not None
    _, selected_c, pipeline, validation_metrics = best
    validation_metrics, validation_rows, validation_probabilities = evaluate_classifier(
        pipeline, validation, "val"
    )
    test_metrics, test_rows, test_probabilities = evaluate_classifier(pipeline, test, "test")

    catalog = d11.copy()
    catalog["profile_text"] = (
        catalog["role_title"].fillna("")
        + ". "
        + catalog["occupation_description"].fillna("")
        + ". "
        + catalog["task_summary"].fillna("")
    )
    catalog[
        [
            "masco_code",
            "masco_code_printed",
            "role_title",
            "source_parent_group_code",
            "flexible_role",
            "profile_text",
        ]
    ].to_csv(D12_DIR / "D12_granular_catalog.csv", index=False)

    fallback_vectorizer = TfidfVectorizer(
        lowercase=True,
        strip_accents="unicode",
        analyzer="char_wb",
        ngram_range=(3, 5),
        min_df=1,
        sublinear_tf=True,
        max_features=80000,
    )
    fallback_matrix = fallback_vectorizer.fit_transform(catalog["profile_text"])

    def fallback_predict(texts: pd.Series) -> tuple[list[str], list[float]]:
        query = fallback_vectorizer.transform(texts.fillna(""))
        scores = query @ fallback_matrix.T
        best_index = np.asarray(scores.argmax(axis=1)).ravel()
        best_score = np.asarray(scores.max(axis=1).toarray()).ravel()
        codes = catalog.iloc[best_index]["masco_code"].astype(str).tolist()
        return codes, [float(value) for value in best_score]

    # Select the threshold on the validation split using the complete two-tier
    # decision, because a confidence threshold that sends every example to a
    # weak fallback is worse than a calibrated low threshold. Ties prefer the
    # highest threshold that does not reduce held-out validation accuracy.
    validation_fallback_codes, _ = fallback_predict(validation["text"])
    threshold_records: list[dict[str, Any]] = []
    for candidate in np.arange(0.00, 0.91, 0.05):
        accepted_mask = validation_rows["classifier_probability"].ge(candidate)
        accepted = validation_rows[accepted_mask]
        final_codes = np.where(
            accepted_mask,
            validation_rows["classifier_masco_code"],
            validation_fallback_codes,
        )
        threshold_records.append(
            {
                "split": "val",
                "threshold": round(float(candidate), 2),
                "accepted_examples": int(accepted_mask.sum()),
                "coverage": round(float(accepted_mask.mean()), 6),
                "accepted_accuracy": (
                    None
                    if accepted.empty
                    else round(float(accepted["classifier_correct"].mean()), 6)
                ),
                "fallback_examples": int((~accepted_mask).sum()),
                "two_tier_accuracy": round(
                    float(
                        np.mean(
                            np.asarray(final_codes)
                            == validation_rows["true_masco_code"].to_numpy()
                        )
                    ),
                    6,
                ),
            }
        )
    threshold_table = pd.DataFrame(threshold_records)
    selected_threshold = threshold_table.sort_values(
        ["two_tier_accuracy", "threshold"], ascending=[False, False]
    ).iloc[0]
    threshold = float(selected_threshold["threshold"])
    threshold_table["selected"] = threshold_table["threshold"].eq(threshold)
    threshold_table.to_csv(D12_DIR / "D12_threshold_calibration.csv", index=False)

    for frame, rows, probs, split in (
        (validation, validation_rows, validation_probabilities, "val"),
        (test, test_rows, test_probabilities, "test"),
    ):
        fallback_codes, fallback_scores = fallback_predict(frame["text"])
        rows["fallback_masco_code"] = fallback_codes
        rows["fallback_similarity"] = np.round(fallback_scores, 6)
        rows["low_confidence"] = rows["classifier_probability"].lt(threshold)
        rows["final_masco_code"] = np.where(
            rows["low_confidence"],
            rows["fallback_masco_code"],
            rows["classifier_masco_code"],
        )
        rows["final_method"] = np.where(
            rows["low_confidence"],
            "character_tfidf_catalog_fallback",
            "word_char_tfidf_logistic_regression",
        )
        rows["final_correct"] = rows["true_masco_code"].eq(rows["final_masco_code"])
        rows.to_csv(D12_DIR / f"D12_{split}_predictions.csv", index=False)

    classes = list(pipeline.named_steps["classifier"].classes_)
    fallback_metrics = {}
    final_metrics = {}
    for split, frame, rows in (
        ("val", validation, validation_rows),
        ("test", test, test_rows),
    ):
        fallback_truth = rows["true_masco_code"].tolist()
        fallback_pred = rows["fallback_masco_code"].tolist()
        fallback_classes = sorted(set(fallback_truth) | set(fallback_pred))
        fallback_metrics[split] = simple_metrics(
            fallback_truth, fallback_pred, fallback_classes
        )
        final_truth = rows["true_masco_code"].tolist()
        final_pred = rows["final_masco_code"].tolist()
        final_classes = sorted(set(final_truth) | set(final_pred))
        final_metrics[split] = simple_metrics(final_truth, final_pred, final_classes)

    # MiniLM class-centroid benchmark over the same JobHop examples/splits.
    all_vectors = np.asarray(
        list(embedder.embed(examples["text"].fillna("").tolist(), batch_size=64))
    )
    train_mask = examples["split"].eq("train").to_numpy()
    centroids: dict[str, np.ndarray] = {}
    for code in classes:
        mask = train_mask & examples["masco_code"].eq(code).to_numpy()
        centroid = all_vectors[mask].mean(axis=0)
        norm = np.linalg.norm(centroid)
        centroids[code] = centroid / norm if norm else centroid
    centroid_rows = [
        {
            "masco_code": code,
            "role_title": d11.set_index("masco_code").loc[code, "role_title"],
            "train_examples": int(
                train["masco_code"].eq(code).sum()
            ),
            "embedding_model": MODEL_NAME,
            "centroid_embedding_384": vector_json(centroids[code]),
        }
        for code in classes
    ]
    pd.DataFrame(centroid_rows).to_csv(D12_DIR / "D12_minilm_class_centroids.csv", index=False)
    minilm_metrics: dict[str, Any] = {}
    for split in ("val", "test"):
        indexes = np.flatnonzero(examples["split"].eq(split).to_numpy())
        predicted = []
        for index in indexes:
            vector = all_vectors[index]
            scores = sorted(
                ((code, float(np.dot(vector, centroids[code]))) for code in classes),
                key=lambda item: item[1],
                reverse=True,
            )
            predicted.append(scores[0][0])
        truth = examples.iloc[indexes]["masco_code"].astype(str).tolist()
        minilm_metrics[split] = simple_metrics(truth, predicted, classes)

    cm = confusion_matrix(
        test_rows["true_masco_code"], test_rows["classifier_masco_code"], labels=classes
    )
    pd.DataFrame(cm, index=classes, columns=classes).rename_axis(
        "actual_masco_code"
    ).reset_index().to_csv(D12_DIR / "D12_confusion_matrix.csv", index=False)

    per_class_rows = []
    for split, metrics in (("val", validation_metrics), ("test", test_metrics)):
        for code, values in metrics["per_class"].items():
            per_class_rows.append({"split": split, "masco_code": code, **values})
    pd.DataFrame(per_class_rows).to_csv(D12_DIR / "D12_per_class_metrics.csv", index=False)

    class_distribution = (
        examples.groupby(["split", "masco_code", "masco_role_title"])
        .agg(examples=("resume_id", "size"), resumes=("resume_id", "nunique"))
        .reset_index()
    )
    class_distribution.to_csv(D12_DIR / "D12_class_distribution.csv", index=False)

    feature_union: FeatureUnion = pipeline.named_steps["features"]
    for name, vectorizer in feature_union.transformer_list:
        vocabulary = pd.DataFrame(
            {
                "feature": vectorizer.get_feature_names_out(),
                "idf": vectorizer.idf_,
            }
        ).sort_values("feature")
        vocabulary.to_csv(D12_DIR / f"D12_{name}_feature_vocabulary.csv", index=False)

    previous_group_metrics = json.loads(D9_METRICS_PATH.read_text(encoding="utf-8"))
    comparison = {
        "granular_classifier_validation": {
            "accuracy": validation_metrics["accuracy"],
            "macro_f1": validation_metrics["macro_f1"],
        },
        "granular_classifier_test": {
            "accuracy": test_metrics["accuracy"],
            "macro_f1": test_metrics["macro_f1"],
        },
        "granular_minilm_centroid": minilm_metrics,
        "prior_group_level_selected_model": previous_group_metrics.get("selected_model"),
        "prior_group_level_validation": previous_group_metrics.get("validation"),
        "prior_group_level_test": previous_group_metrics.get("test"),
        "comparability_note": (
            "Group-level and six-digit granular metrics have different label spaces and "
            "are reported side by side, not as a like-for-like improvement claim."
        ),
    }
    selected_research_model = (
        "minilm_centroid_retrieval"
        if minilm_metrics["val"]["macro_f1"] > validation_metrics["macro_f1"]
        else "word_char_tfidf_balanced_logistic_regression"
    )

    artifact = {
        "format_version": 2,
        "task": "D12 six-digit MASCO occupation classifier",
        "label_regex": LABEL_PATTERN,
        "resume_dataset": "JobHop v2 confirmed active 2019+ only",
        "resume_dataset_sha256": profile["jobhop_source_sha256"],
        "pipeline": pipeline,
        "fallback_vectorizer": fallback_vectorizer,
        "fallback_catalog_matrix": fallback_matrix,
        "catalog": catalog[
            [
                "masco_code",
                "masco_code_printed",
                "role_title",
                "source_parent_group_code",
                "flexible_role",
                "profile_text",
            ]
        ].to_dict("records"),
        "classes": classes,
        "low_confidence_threshold": threshold,
        "embedding_model": MODEL_NAME,
        "embedding_class_centroids": {
            code: np.asarray(centroids[code], dtype=float) for code in classes
        },
        "selected_research_model": selected_research_model,
        "selection_metric": "validation macro-F1",
        "compose_text_format": profile["feature_scope"],
        "sparsity_policy": (
            f"Premerge classes with fewer than {MIN_TRAIN_SUPPORT} train examples "
            "merge to the curated six-digit anchor in the same MASCO parent group."
        ),
        "random_state": RANDOM_STATE,
    }
    joblib.dump(artifact, D12_DIR / "D12_granular_masco_classifier.joblib")

    metrics = {
        "task": "D12",
        "model": "word + char_wb TF-IDF with balanced logistic regression",
        "resume_dataset_policy": profile["resume_dataset_policy"],
        "jobhop_source_sha256": profile["jobhop_source_sha256"],
        "raw_resume_text_available": False,
        "label_rule": "all model classes and predictions are exactly six-digit MASCO codes",
        "selected_C": selected_c,
        "grid_results": grid_results,
        "low_confidence_threshold": threshold,
        "class_count": len(classes),
        "classes": classes,
        "validation": validation_metrics,
        "test": test_metrics,
        "character_tfidf_full_catalog_fallback": fallback_metrics,
        "two_tier_final": final_metrics,
        "minilm_centroid_benchmark": minilm_metrics,
        "selected_research_model": selected_research_model,
        "selection_metric": "validation macro-F1",
        "group_level_comparison": comparison,
        "catalog_size": len(catalog),
        "scikit_learn_version": sklearn.__version__,
        "embedding_model": MODEL_NAME,
        "production_approved": False,
        "production_blockers": [
            "The JobHop input contains structured Belgian/Flemish career histories, not raw Malaysian CV text.",
            "The project ESCO-to-six-digit-MASCO crosswalk requires domain-owner review.",
            "Several sparse granular labels are merged to six-digit curated anchors.",
            "Child-level remote/AI ratings inherit unit-group pre-ratings pending two-rater review.",
        ],
    }
    write_json(D12_DIR / "D12_metrics.json", metrics)
    write_json(
        D12_DIR / "D12_inference_policy.json",
        {
            "label_format": "six ASCII digits",
            "label_regex": LABEL_PATTERN,
            "primary_model": "word + char_wb TF-IDF balanced logistic regression",
            "validation_benchmark_winner": selected_research_model,
            "selection_metric": "validation macro-F1",
            "deployment_note": (
                "The benchmark winner is recorded for research comparison; no model is "
                "approved for automatic production use."
            ),
            "low_confidence_threshold": threshold,
            "fallback": "character char_wb TF-IDF retrieval over the complete D11 catalog",
            "decision": (
                "Use classifier prediction when probability >= threshold; otherwise "
                "return catalog fallback as a suggestion requiring user confirmation."
            ),
            "human_confirmation_required": True,
            "automatic_employment_decision_use": False,
            "input_contract": (
                "Structured prior occupation titles, optional ESCO skill groups, durations, "
                "and education; do not represent this artifact as a raw-CV model."
            ),
            "resume_dataset": "JobHop v2 confirmed active 2019+ only",
        },
    )
    return metrics


def build_migration_sql(d11: pd.DataFrame) -> None:
    columns = [
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
        "role_embedding",
    ]
    tuples = []
    for row in d11.to_dict("records"):
        values = {
            **row,
            "role_embedding": "{" + ",".join(
                format(float(value), ".9g")
                for value in json.loads(row["role_embedding_384"])
            ) + "}",
        }
        tuples.append(
            "(" + ",".join(sql_literal(values.get(column)) for column in columns) + ")"
        )

    sql = f"""-- D11 migration: six-digit MASCO roles only.
-- Generated by 04_REPRODUCIBILITY/build_d11_d12.py.
-- Existing R01-R10 rows are updated to their six-digit anchor occupations;
-- all other granular children are inserted. Four-digit MASCO group codes are
-- lineage only and are not written to rerouteher.roles.masco_code.

BEGIN;

ALTER TABLE rerouteher.roles ALTER COLUMN masco_code TYPE text;
ALTER TABLE rerouteher.roles ALTER COLUMN isco08_code DROP NOT NULL;
ALTER TABLE rerouteher.roles ALTER COLUMN esco_code DROP NOT NULL;
ALTER TABLE rerouteher.roles ALTER COLUMN onet_code DROP NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS roles_masco_code_six_digit_uq
    ON rerouteher.roles (masco_code);

INSERT INTO rerouteher.roles ({','.join(columns)}) VALUES
{',\n'.join(tuples)}
ON CONFLICT (role_id) DO UPDATE SET
    role_title = EXCLUDED.role_title,
    masco_code = EXCLUDED.masco_code,
    masco_title = EXCLUDED.masco_title,
    task_summary = EXCLUDED.task_summary,
    occupation_description = EXCLUDED.occupation_description,
    remote_possibility = EXCLUDED.remote_possibility,
    remote_task_count = EXCLUDED.remote_task_count,
    remote_capable_tasks = EXCLUDED.remote_capable_tasks,
    remote_onsite_tasks = EXCLUDED.remote_onsite_tasks,
    remote_unclear_tasks = EXCLUDED.remote_unclear_tasks,
    remote_justification = EXCLUDED.remote_justification,
    ai_exposure = EXCLUDED.ai_exposure,
    ai_exposure_share = EXCLUDED.ai_exposure_share,
    ai_exposure_measure = EXCLUDED.ai_exposure_measure,
    flexible_role = EXCLUDED.flexible_role,
    rating_status = EXCLUDED.rating_status,
    embedding_model = EXCLUDED.embedding_model,
    role_embedding = EXCLUDED.role_embedding;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM rerouteher.roles
        WHERE masco_code !~ '^\\d{{6}}$'
    ) THEN
        RAISE EXCEPTION 'D11 migration left a non-six-digit MASCO role code';
    END IF;
END $$;

COMMIT;
"""
    (DATABASE_DIR / "D11_roles_six_digit_migration.sql").write_text(sql, encoding="utf-8")


def build_source_manifest() -> pd.DataFrame:
    sources = [
        (JOBHOP_PATH, "sole resume/career-history dataset"),
        (JOBHOP_AUDIT_PATH, "approved JobHop processing audit"),
        (MASCO_PDF_PATH, "occupation codes, titles, descriptions and tasks"),
        (ESCO_ONET_PATH, "non-resume ESCO occupation-title reference"),
        (D1_ROLES_PATH, "D1 unit-group rating and task-text lineage"),
        (ESCO_PROFILES_PATH, "non-resume ESCO skill-group reference"),
    ]
    rows = []
    for path, purpose in sources:
        rows.append(
            {
                "relative_path": str(path.relative_to(WORKSPACE)),
                "purpose": purpose,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
                "resume_dataset": path == JOBHOP_PATH,
            }
        )
    manifest = pd.DataFrame(rows)
    manifest.to_csv(QA_DIR / "D11_D12_source_manifest.csv", index=False)
    return manifest


def main() -> None:
    required = [
        JOBHOP_PATH,
        JOBHOP_AUDIT_PATH,
        MASCO_PDF_PATH,
        ESCO_ONET_PATH,
        D1_ROLES_PATH,
        ESCO_PROFILES_PATH,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Required source files missing: {missing}")
    embedder = TextEmbedding(model_name=MODEL_NAME, cache_dir=str(EMBEDDING_CACHE))
    d11, d11_audit = build_d11(embedder)
    examples, _, profile = build_jobhop_examples(d11)
    d12_metrics = build_d12(d11, examples, profile, embedder)
    manifest = build_source_manifest()
    summary = {
        "d11_granular_roles": len(d11),
        "d11_all_codes_six_digit": d11_audit["all_codes_six_digit"],
        "d12_training_examples": len(examples),
        "d12_model_classes": d12_metrics["class_count"],
        "d12_catalog_size": d12_metrics["catalog_size"],
        "d12_validation_accuracy": d12_metrics["validation"]["accuracy"],
        "d12_test_accuracy": d12_metrics["test"]["accuracy"],
        "resume_dataset": "JobHop v2 confirmed active 2019+ only",
        "source_files": len(manifest),
    }
    write_json(QA_DIR / "D11_D12_build_summary.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
