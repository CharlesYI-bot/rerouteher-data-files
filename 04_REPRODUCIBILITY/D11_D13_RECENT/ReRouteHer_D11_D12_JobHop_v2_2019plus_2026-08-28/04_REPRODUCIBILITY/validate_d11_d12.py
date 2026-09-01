from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = PACKAGE_ROOT.parent
sys.path.insert(0, str(WORKSPACE / ".work" / "sklearn"))

import joblib  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


D11_DIR = PACKAGE_ROOT / "01_D11_REFERENCE_TABLES"
D12_DIR = PACKAGE_ROOT / "02_D12_MODEL"
DATABASE_DIR = PACKAGE_ROOT / "03_DATABASE"
QA_DIR = PACKAGE_ROOT / "05_QA"
LABEL_PATTERN = re.compile(r"^\d{6}$")
EXPECTED_GROUP_COUNTS = {
    "2311": 42,
    "2423": 25,
    "2431": 41,
    "2512": 47,
    "2524": 21,
    "2543": 19,
    "2833": 10,
    "4121": 13,
    "4222": 7,
    "4311": 33,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    checks: list[dict[str, object]] = []

    def check(check_id: str, condition: bool, evidence: object) -> None:
        checks.append(
            {
                "check_id": check_id,
                "status": "PASS" if bool(condition) else "FAIL",
                "evidence": json.dumps(evidence, ensure_ascii=False)
                if not isinstance(evidence, str)
                else evidence,
            }
        )

    d11 = pd.read_csv(
        D11_DIR / "D11_masco_granular_roles.csv",
        dtype={
            "role_id": str,
            "masco_code": str,
            "masco_code_printed": str,
            "source_parent_group_code": str,
        },
        keep_default_na=False,
    )
    check("D11_ROW_COUNT", len(d11) == 258, len(d11))
    check("D11_UNIQUE_CODES", d11["masco_code"].nunique() == len(d11), len(d11))
    check(
        "D11_ALL_CODES_SIX_DIGIT",
        d11["masco_code"].map(lambda value: bool(LABEL_PATTERN.fullmatch(value))).all(),
        {"invalid": d11.loc[~d11["masco_code"].str.fullmatch(r"\d{6}"), "masco_code"].tolist()},
    )
    check(
        "D11_PRINTED_CODE_MATCHES",
        d11.apply(
            lambda row: row["masco_code_printed"]
            == f"{row['masco_code'][:4]}-{row['masco_code'][4:]}",
            axis=1,
        ).all(),
        "six-digit storage and printed MASCO hyphen agree",
    )
    group_counts = (
        d11.groupby("source_parent_group_code").size().astype(int).sort_index().to_dict()
    )
    check("D11_GROUP_COUNTS", group_counts == EXPECTED_GROUP_COUNTS, group_counts)
    check("D11_TEN_FLEXIBLE_ANCHORS", int(d11["flexible_role"].sum()) == 10, int(d11["flexible_role"].sum()))
    check(
        "D11_MISSING_NOT_ZERO",
        not d11[["isco08_code", "esco_code", "onet_code", "remote_external_proxy"]]
        .astype(str)
        .apply(lambda column: column.str.fullmatch("0").any())
        .any(),
        "nullable identifier/proxy fields use blank/null, not 0, as the missing-value sentinel",
    )
    vectors = [np.asarray(json.loads(value), dtype=float) for value in d11["role_embedding_384"]]
    vector_shape_ok = all(vector.shape == (384,) for vector in vectors)
    finite_ok = all(np.isfinite(vector).all() for vector in vectors)
    check("D11_EMBEDDING_DIMENSIONS", vector_shape_ok and finite_ok, {"rows": len(vectors), "dimension": 384})
    check(
        "D11_EMBEDDING_MODEL",
        d11["embedding_model"].eq("sentence-transformers/all-MiniLM-L6-v2").all(),
        d11["embedding_model"].value_counts().to_dict(),
    )

    examples = pd.read_csv(
        D12_DIR / "D12_training_examples_jobhop_v2_2019plus.csv",
        dtype={
            "resume_id": str,
            "masco_code": str,
            "premerge_masco_code": str,
            "target_esco_code": str,
        },
        keep_default_na=False,
    )
    d11_codes = set(d11["masco_code"])
    check("D12_EXAMPLE_COUNT", len(examples) == 562, len(examples))
    check("D12_ONE_EXAMPLE_PER_RESUME", examples["resume_id"].nunique() == len(examples), examples["resume_id"].nunique())
    check(
        "D12_PRESERVED_SPLITS",
        examples["split"].value_counts().sort_index().to_dict()
        == {"test": 45, "train": 455, "val": 62},
        examples["split"].value_counts().sort_index().to_dict(),
    )
    check(
        "D12_ALL_TRAINING_LABELS_SIX_DIGIT",
        examples["masco_code"].map(lambda value: bool(LABEL_PATTERN.fullmatch(value))).all(),
        sorted(examples["masco_code"].unique()),
    )
    check(
        "D12_LABELS_EXIST_IN_D11",
        set(examples["masco_code"]).issubset(d11_codes),
        sorted(set(examples["masco_code"]) - d11_codes),
    )
    check(
        "D12_TARGET_EXCLUDED_FROM_TEXT",
        not examples.apply(
            lambda row: row["target_esco_title"].lower() in row["text"].lower(), axis=1
        ).all(),
        "latest target is not systematically leaked into composed prior-history text",
    )

    profile = json.loads((D12_DIR / "D12_dataset_profile.json").read_text(encoding="utf-8"))
    jobhop_path = WORKSPACE / profile["jobhop_source"]
    check(
        "D12_JOBHOP_HASH_MATCH",
        jobhop_path.exists() and sha256(jobhop_path) == profile["jobhop_source_sha256"],
        profile["jobhop_source_sha256"],
    )
    check(
        "D12_SOLE_RESUME_DATASET_POLICY",
        profile["resume_dataset_policy"]
        == "JobHop v2 confirmed-active 2019+ is the sole resume/career-history dataset.",
        profile["resume_dataset_policy"],
    )
    manifest = pd.read_csv(QA_DIR / "D11_D12_source_manifest.csv")
    resume_sources = manifest[manifest["resume_dataset"].astype(str).str.lower().eq("true")]
    check(
        "D12_ONE_RESUME_SOURCE_IN_MANIFEST",
        len(resume_sources) == 1
        and "jobhop_v2_confirmed_active_2019plus.csv"
        in str(resume_sources.iloc[0]["relative_path"]),
        resume_sources["relative_path"].tolist(),
    )

    crosswalk = pd.read_csv(
        D12_DIR / "D12_esco_to_masco_label_crosswalk.csv",
        dtype={"premerge_masco_code": str, "masco_code": str},
        keep_default_na=False,
    )
    check("D12_CROSSWALK_70_TARGET_CODES", crosswalk["target_esco_code"].nunique() == 70, crosswalk["target_esco_code"].nunique())
    check(
        "D12_CROSSWALK_LABELS_EXIST_IN_D11",
        set(crosswalk["premerge_masco_code"]).issubset(d11_codes)
        and set(crosswalk["masco_code"]).issubset(d11_codes),
        "all premerge and model labels resolve to D11",
    )

    artifact_path = D12_DIR / "D12_granular_masco_classifier.joblib"
    artifact = joblib.load(artifact_path)
    required_keys = {
        "pipeline",
        "fallback_vectorizer",
        "fallback_catalog_matrix",
        "catalog",
        "threshold",
        "classes",
    }
    # Artifact uses an explicit low_confidence_threshold key.
    required_keys.remove("threshold")
    required_keys.add("low_confidence_threshold")
    check("D12_ARTIFACT_STRUCTURE", required_keys.issubset(artifact), sorted(artifact.keys()))
    artifact_classes = [str(value) for value in artifact["classes"]]
    check(
        "D12_ARTIFACT_CLASSES_SIX_DIGIT",
        all(LABEL_PATTERN.fullmatch(value) for value in artifact_classes),
        artifact_classes,
    )
    check(
        "D12_ARTIFACT_CLASSES_IN_D11",
        set(artifact_classes).issubset(d11_codes),
        sorted(set(artifact_classes) - d11_codes),
    )
    check(
        "D12_FULL_FALLBACK_CATALOG",
        len(artifact["catalog"]) == 258
        and artifact["fallback_catalog_matrix"].shape[0] == 258,
        {
            "catalog": len(artifact["catalog"]),
            "matrix_rows": artifact["fallback_catalog_matrix"].shape[0],
        },
    )

    test = examples[examples["split"].eq("test")].copy()
    predicted = artifact["pipeline"].predict(test["text"])
    prediction_file = pd.read_csv(
        D12_DIR / "D12_test_predictions.csv",
        dtype={
            "true_masco_code": str,
            "classifier_masco_code": str,
            "fallback_masco_code": str,
            "final_masco_code": str,
        },
    )
    check(
        "D12_ARTIFACT_REPRODUCES_TEST_PREDICTIONS",
        list(predicted) == prediction_file["classifier_masco_code"].tolist(),
        {"predictions": len(predicted)},
    )
    check(
        "D12_ALL_REPORTED_PREDICTIONS_SIX_DIGIT",
        all(
            prediction_file[column].map(
                lambda value: bool(LABEL_PATTERN.fullmatch(str(value)))
            ).all()
            for column in [
                "true_masco_code",
                "classifier_masco_code",
                "fallback_masco_code",
                "final_masco_code",
            ]
        ),
        "true, classifier, fallback and final codes all use six digits",
    )
    check(
        "D12_ALL_REPORTED_PREDICTIONS_IN_D11",
        all(
            set(prediction_file[column]).issubset(d11_codes)
            for column in [
                "true_masco_code",
                "classifier_masco_code",
                "fallback_masco_code",
                "final_masco_code",
            ]
        ),
        "all reported labels resolve to D11 catalog",
    )

    metrics = json.loads((D12_DIR / "D12_metrics.json").read_text(encoding="utf-8"))
    check("D12_NOT_PRODUCTION_APPROVED", metrics["production_approved"] is False, metrics["production_blockers"])
    check(
        "D12_METRICS_HONEST_SCOPE",
        metrics["raw_resume_text_available"] is False
        and metrics["resume_dataset_policy"].endswith("sole resume/career-history dataset.")
        and metrics["selected_research_model"] == "minilm_centroid_retrieval",
        {
            "resume_dataset_policy": metrics["resume_dataset_policy"],
            "selected_research_model": metrics["selected_research_model"],
        },
    )

    migration = (DATABASE_DIR / "D11_roles_six_digit_migration.sql").read_text(encoding="utf-8")
    check(
        "D11_MIGRATION_SIX_DIGIT_GUARD",
        "masco_code !~ '^\\d{6}$'" in migration,
        "migration fails if any roles.masco_code is not six digits",
    )
    check(
        "D11_MIGRATION_CONTAINS_ALL_CODES",
        all(f"'{code}'" in migration for code in d11_codes),
        {"codes": len(d11_codes)},
    )

    failed = [row for row in checks if row["status"] == "FAIL"]
    report = {
        "task_scope": "D11 and D12",
        "status": "PASS" if not failed else "FAIL",
        "checks": len(checks),
        "passed": len(checks) - len(failed),
        "failed": len(failed),
        "d11_roles": len(d11),
        "d12_training_examples": len(examples),
        "d12_model_classes": len(artifact_classes),
        "d12_catalog_size": len(artifact["catalog"]),
        "resume_dataset": "JobHop v2 confirmed active 2019+ only",
        "failed_checks": [row["check_id"] for row in failed],
    }
    QA_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(checks).to_csv(QA_DIR / "D11_D12_validation_checks.csv", index=False)
    (QA_DIR / "D11_D12_validation_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    checksum_path = PACKAGE_ROOT / "D11_D12_OUTPUT_SHA256SUMS.txt"
    checksum_lines = []
    for path in sorted(PACKAGE_ROOT.rglob("*")):
        if (
            not path.is_file()
            or "__pycache__" in path.parts
            or path == checksum_path
        ):
            continue
        checksum_lines.append(f"{sha256(path)}  {path.relative_to(PACKAGE_ROOT)}")
    checksum_path.write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
