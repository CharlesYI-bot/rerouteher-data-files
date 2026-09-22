#!/usr/bin/env python3
"""Validate the Iteration 3 Interview Assistant release package."""

from __future__ import annotations

import csv
import hashlib
import json
import zipfile
from collections import Counter
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO = SCRIPT_DIR.parents[2]
RAW = REPO / "02_RAW_SOURCE_DATA" / "ITERATION_3" / "INTERVIEW_ASSISTANT"
PROCESSED = REPO / "03_PROCESSED_DATA" / "ITERATION_3" / "INTERVIEW_ASSISTANT"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(name: str) -> list[dict[str, str]]:
    with (PROCESSED / "csv" / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    checks: list[tuple[str, bool, object]] = []

    with (RAW / "source_manifest.csv").open(encoding="utf-8", newline="") as handle:
        manifest = list(csv.DictReader(handle))
    checks.append(("raw source manifest count", len(manifest) == 17, len(manifest)))
    for row in manifest:
        file_path = RAW / row["local_file"]
        checks.append((f"source exists: {row['local_file']}", file_path.is_file(), file_path.is_file()))
        if file_path.is_file():
            checks.append((f"source bytes: {row['local_file']}", file_path.stat().st_size == int(row["bytes"]), file_path.stat().st_size))
            checks.append((f"source hash: {row['local_file']}", sha256(file_path) == row["sha256"], sha256(file_path)))

    roles = read_csv("masco_roles.csv")
    questions = read_csv("interview_qa.csv")
    matches = read_csv("global_matches.csv")
    anchors = read_csv("role_anchors.csv")
    open_qa = read_csv("open_qa.csv")
    links = read_csv("open_qa_links.csv")
    quality = read_csv("data_quality.csv")
    expected_counts = {
        "roles": (len(roles), 657),
        "questions": (len(questions), 7884),
        "matches": (len(matches), 1078),
        "anchors": (len(anchors), 5581),
        "open_qa": (len(open_qa), 142),
        "links": (len(links), 320),
    }
    for label, (actual, expected) in expected_counts.items():
        checks.append((f"{label} count", actual == expected, actual))

    role_ids = {row["role_id"] for row in roles}
    checks.append(("unique role ids", len(role_ids) == 657, len(role_ids)))
    checks.append(("question ids unique", len({row["question_id"] for row in questions}) == len(questions), len(questions)))
    checks.append(("questions use MASCO roles only", {row["role_id"] for row in questions} == role_ids, len({row["role_id"] for row in questions})))
    per_role = Counter(row["role_id"] for row in questions)
    checks.append(("12 questions per role", set(per_role.values()) == {12}, sorted(set(per_role.values()))))
    checks.append(("quality checks pass", len(quality) == 11 and all(row["status"] == "PASS" for row in quality), Counter(row["status"] for row in quality)))

    workbook = PROCESSED / "ReRouteHer_MASCO657_Global_Interview_Dataset_v3.xlsx"
    with zipfile.ZipFile(workbook) as archive:
        bad_member = archive.testzip()
    checks.append(("workbook archive integrity", bad_member is None, bad_member))

    release = json.loads((PROCESSED / "release_summary.json").read_text(encoding="utf-8"))
    checks.append(("release workbook hash", release["workbook_sha256"] == sha256(workbook), sha256(workbook)))

    failed = [check for check in checks if not check[1]]
    print(json.dumps({"checks": len(checks), "passed": len(checks) - len(failed), "failed": failed}, indent=2, default=str))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
