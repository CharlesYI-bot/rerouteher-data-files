#!/usr/bin/env python3
"""Create a reproducible structured snapshot of the official eMASCO STEM directory.

The portal is server-rendered and robots.txt permits crawling. Requests are made
serially with a delay and a descriptive User-Agent. The output is JSON source
evidence; D1-compatible transformation happens in build_d11_stem_tables.py.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from lxml import html


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "00_SOURCE_SNAPSHOT"
SNAPSHOT_PATH = SOURCE_DIR / "emasco_stem_occupations_2026-08-29.json"
PARTIAL_PATH = SOURCE_DIR / "emasco_stem_occupations_2026-08-29.partial.json"
BASE_URL = "https://emasco.mohr.gov.my"
STEM_URL = f"{BASE_URL}/directory/category/stem?lang=en"
CODE_PRINTED_PATTERN = re.compile(r"^\d{4}-\d{2}$")


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def atomic_json(path: Path, payload: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


class EmascoClient:
    def __init__(self, delay_seconds: float) -> None:
        self.delay_seconds = delay_seconds
        self.cookie_path = SOURCE_DIR / ".emasco_cookies.txt"
        self.unit_group_cache: dict[str, dict[str, Any]] = {}

    def fetch(self, url: str) -> tuple[str, str, str]:
        delimiter = b"\n__REROUTEHER_FINAL_URL__:"
        last_error: Exception | None = None
        for attempt in range(1, 4):
            try:
                result = subprocess.run(
                    [
                        "/usr/bin/curl",
                        "--fail",
                        "--silent",
                        "--show-error",
                        "--location",
                        "--max-time",
                        "30",
                        "--user-agent",
                        (
                            "ReRouteHer-D11-STEM-research/1.0 "
                            "(serial public-taxonomy extraction)"
                        ),
                        "--cookie",
                        str(self.cookie_path),
                        "--cookie-jar",
                        str(self.cookie_path),
                        "--write-out",
                        "\n__REROUTEHER_FINAL_URL__:%{url_effective}",
                        url,
                    ],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                raw, final_raw = result.stdout.rsplit(delimiter, 1)
                final_url = final_raw.decode("utf-8", errors="replace").strip()
                text = raw.decode("utf-8", errors="replace")
                digest = hashlib.sha256(raw).hexdigest()
                time.sleep(self.delay_seconds)
                return text, final_url, digest
            except (subprocess.CalledProcessError, ValueError) as exc:
                last_error = exc
                if attempt == 3:
                    break
                time.sleep(attempt * 2)
        raise RuntimeError(f"Unable to fetch {url}: {last_error}")


def directory_rows(client: EmascoClient) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    page_url: str | None = STEM_URL
    rows: list[dict[str, str]] = []
    page_manifest: list[dict[str, str]] = []
    while page_url:
        text, final_url, digest = client.fetch(page_url)
        document = html.fromstring(text)
        page_number = len(page_manifest) + 1
        page_manifest.append(
            {
                "page_type": "stem_directory",
                "page_number": str(page_number),
                "source_url": final_url,
                "sha256": digest,
            }
        )
        page_rows = document.xpath("//table//tbody/tr")
        for element in page_rows:
            cells = [clean(cell.text_content()) for cell in element.xpath("./td")]
            if len(cells) < 2 or not CODE_PRINTED_PATTERN.fullmatch(cells[0]):
                continue
            onclick = element.get("onclick", "")
            match = re.search(r"window\.location='([^']+)'", onclick)
            detail_url = match.group(1) if match else f"{BASE_URL}/masco/{cells[0]}"
            rows.append(
                {
                    "masco_code_printed": cells[0],
                    "masco_code": cells[0].replace("-", ""),
                    "directory_role_title": cells[1],
                    "detail_url": detail_url,
                }
            )
        next_nodes = document.xpath("//a[normalize-space(.)='»']/@href")
        page_url = urljoin(BASE_URL, next_nodes[0]) if next_nodes else None

    codes = [row["masco_code"] for row in rows]
    if len(rows) != 657 or len(set(codes)) != 657:
        raise AssertionError(
            f"Official STEM directory contract changed: rows={len(rows)}, unique={len(set(codes))}."
        )
    return rows, page_manifest


def hierarchy_title(document: Any, code: str) -> str:
    nodes = document.xpath(f"//main//a[@href='/masco/{code}']")
    if not nodes:
        return ""
    value = clean(nodes[0].text_content())
    return re.sub(rf"^{re.escape(code)}\s+", "", value)


def parse_detail(
    client: EmascoClient, directory_row: dict[str, str]
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    text, final_url, digest = client.fetch(directory_row["detail_url"])
    document = html.fromstring(text)
    title_nodes = document.xpath(
        "//main//div[contains(@class,'font-bold') and contains(@class,'text-3xl')]"
    )
    description_nodes = document.xpath(
        "//main//div[contains(@class,'mb-10') and contains(@class,'text-lg')]"
    )
    task_nodes = document.xpath(
        "//main//div[contains(@class,'first-letter:uppercase')]"
    )
    if not title_nodes or not description_nodes:
        raise AssertionError(
            f"Missing required title/description on {directory_row['detail_url']}"
        )

    code_printed = directory_row["masco_code_printed"]
    code = directory_row["masco_code"]
    categories = sorted(
        {
            href.rsplit("/", 1)[-1]
            for href in document.xpath("//main//a[starts-with(@href,'/directory/category/')]/@href")
        }
    )
    detail_manifest = [
        {
            "page_type": "occupation_detail",
            "masco_code": code,
            "source_url": final_url,
            "sha256": digest,
        }
    ]
    if task_nodes:
        tasks = [clean(node.text_content()) for node in task_nodes]
        tasks_source_level = "exact_occupation"
        tasks_source_url = final_url
        tasks_source_sha256 = digest
    else:
        unit_group_code = code[:4]
        if unit_group_code not in client.unit_group_cache:
            group_url = f"{BASE_URL}/masco/{unit_group_code}"
            group_text, group_final_url, group_digest = client.fetch(group_url)
            group_document = html.fromstring(group_text)
            group_task_nodes = group_document.xpath(
                "//main//div[contains(@class,'first-letter:uppercase')]"
            )
            if not group_task_nodes:
                raise AssertionError(
                    f"Exact role and unit group both lack tasks: {directory_row['detail_url']}"
                )
            client.unit_group_cache[unit_group_code] = {
                "tasks": [clean(node.text_content()) for node in group_task_nodes],
                "source_url": group_final_url,
                "sha256": group_digest,
            }
            detail_manifest.append(
                {
                    "page_type": "unit_group_task_fallback",
                    "masco_code": unit_group_code,
                    "source_url": group_final_url,
                    "sha256": group_digest,
                }
            )
        group = client.unit_group_cache[unit_group_code]
        tasks = group["tasks"]
        tasks_source_level = "unit_group_inherited"
        tasks_source_url = group["source_url"]
        tasks_source_sha256 = group["sha256"]

    role = {
        **directory_row,
        "role_title": clean(title_nodes[0].text_content()),
        "occupation_description": clean(description_nodes[0].text_content()),
        "tasks": tasks,
        "tasks_source_level": tasks_source_level,
        "tasks_source_url": tasks_source_url,
        "tasks_source_page_sha256": tasks_source_sha256,
        "major_group_code": code[:1],
        "major_group_title": hierarchy_title(document, code[:1]),
        "sub_major_group_code": code[:2],
        "sub_major_group_title": hierarchy_title(document, code[:2]),
        "minor_group_code": code[:3],
        "minor_group_title": hierarchy_title(document, code[:3]),
        "unit_group_code": code[:4],
        "unit_group_title": hierarchy_title(document, code[:4]),
        "categories": categories,
        "source_url": final_url,
        "source_page_sha256": digest,
    }
    if "stem" not in categories:
        raise AssertionError(f"STEM marker missing on detail record {code_printed}.")
    if role["role_title"].casefold() != directory_row["directory_role_title"].casefold():
        role["title_comparison_status"] = "directory_detail_title_difference"
    else:
        role["title_comparison_status"] = "exact"
    return role, detail_manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--delay-seconds", type=float, default=0.10)
    args = parser.parse_args()
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    client = EmascoClient(max(0.05, args.delay_seconds))
    directory, manifest = directory_rows(client)
    print(f"Verified {len(directory)} unique STEM directory entries across {len(manifest)} pages.", flush=True)

    existing: dict[str, dict[str, Any]] = {}
    if PARTIAL_PATH.exists():
        partial = json.loads(PARTIAL_PATH.read_text(encoding="utf-8"))
        existing = {row["masco_code"]: row for row in partial.get("occupations", [])}

    roles: list[dict[str, Any]] = []
    detail_manifest: list[dict[str, str]] = []
    for index, row in enumerate(directory, 1):
        if row["masco_code"] in existing:
            role = existing[row["masco_code"]]
            role.setdefault("tasks_source_level", "exact_occupation")
            role.setdefault("tasks_source_url", role["source_url"])
            role.setdefault("tasks_source_page_sha256", role["source_page_sha256"])
            detail_manifest.append(
                {
                    "page_type": "occupation_detail",
                    "masco_code": role["masco_code"],
                    "source_url": role["source_url"],
                    "sha256": role["source_page_sha256"],
                }
            )
        else:
            role, detail_sources = parse_detail(client, row)
            detail_manifest.extend(detail_sources)
        roles.append(role)
        if index % 25 == 0 or index == len(directory):
            atomic_json(
                PARTIAL_PATH,
                {
                    "status": "partial",
                    "occupations": roles,
                },
            )
            print(f"Fetched {index}/{len(directory)} occupation details.", flush=True)

    retrieved_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    payload = {
        "schema_version": 1,
        "status": "complete",
        "source_name": "eMASCO STEM occupation directory",
        "source_authority": "Ministry of Human Resources Malaysia (KESUMA)",
        "source_url": "https://emasco.mohr.gov.my/directory/category/stem",
        "source_definition": (
            "Occupation that includes Science, Technology, Engineering or Mathematics element"
        ),
        "portal_content_basis": "MASCO 2020",
        "portal_notice": (
            "The new portal states that it is undergoing enhancement and that its current "
            "content remains based on MASCO 2020."
        ),
        "source_retrieved_at": retrieved_at,
        "directory_page_count": len(manifest),
        "occupation_count": len(roles),
        "occupations": roles,
        "page_manifest": manifest + detail_manifest,
    }
    atomic_json(SNAPSHOT_PATH, payload)
    PARTIAL_PATH.unlink(missing_ok=True)
    client.cookie_path.unlink(missing_ok=True)
    print(f"Wrote {SNAPSHOT_PATH}", flush=True)


if __name__ == "__main__":
    main()
