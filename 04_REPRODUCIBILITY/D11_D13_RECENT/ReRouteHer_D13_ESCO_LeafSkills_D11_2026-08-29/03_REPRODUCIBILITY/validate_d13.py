#!/usr/bin/env python3
"""Independent structural checks for the D13 release outputs."""

from __future__ import annotations

import csv
import json
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "01_TABLES"


def rows(name: str) -> list[dict[str, str]]:
    with (TABLES / name).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    coverage = rows("D13_role_esco_coverage.csv")
    taxonomy = rows("skill_taxonomy.csv")
    aliases = rows("skill_aliases.csv")
    role_skills = rows("role_skills.csv")
    lineage = rows("role_skills_lineage.csv")
    assert len(coverage) == 657
    assert all(re.fullmatch(r"\d{6}", row["masco_code"]) for row in coverage)
    assert len({row["role_id"] for row in coverage}) == 657
    assert {row["importance"] for row in role_skills} <= {"50", "100"}
    assert len({(row["role_id"], row["skill_id"]) for row in role_skills}) == len(role_skills)
    assert {(row["role_id"], row["skill_id"]) for row in role_skills} == {
        (row["role_id"], row["skill_id"]) for row in lineage
    }
    assert {row["skill_id"] for row in taxonomy} == {row["skill_id"] for row in role_skills}
    assert all(row["skill_type"] for row in taxonomy)
    assert len({(row["skill_id"], row["alias"].casefold()) for row in aliases}) == len(aliases)
    for row in taxonomy:
        vector = [float(value) for value in row["embedding"].strip("[]").split(",")]
        assert len(vector) == 384
        assert math.isclose(sum(value * value for value in vector), 1.0, abs_tol=2e-5)
    assert all(row["source_version"] == "ESCO v1.2.1" for row in lineage)
    result = {
        "status": "PASS",
        "roles": len(coverage),
        "mapped_roles": sum(row["use_in_role_skills"] == "True" for row in coverage),
        "skills": len(taxonomy),
        "aliases": len(aliases),
        "role_skills": len(role_skills),
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
