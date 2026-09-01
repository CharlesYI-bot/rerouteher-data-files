from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
EMP = ROOT / "03_EMPLOYER_EVIDENCE"
DMP = ROOT / "05_DMP"
ARCHIVE = EMP / "archive"


NEW_REPORTS = [
    {
        "employer_id": "1155",
        "name": "Malayan Banking Berhad",
        "report_year": "2025",
        "report_url": "https://maybankfoundation.com/wp-content/uploads/2026/04/maybank-sustainability-and-environmental-report-2025.pdf",
        "page_or_section": "p. 120, Empowering Our People",
        "maternity_days": "98",
        "flexible_remote_disclosed": "True",
        "childcare_nursing_phased_return": "True",
        "evidence_note": "Maybank discloses 98 days of maternity leave with an extension option, flexible-work arrangements, childcare centres/benefits and equipped nursing rooms.",
    },
    {
        "employer_id": "1961",
        "name": "IOI Corporation Berhad",
        "report_year": "2025",
        "report_url": "https://www.ioigroup.com/integrated-report/sr/2025/pdf/IOIG_SR25_Fullbook%28Single%20Page%29.pdf",
        "page_or_section": "Gender Equality and Women Empowerment; Women Empowerment Committee",
        "evidence_note": "The report was reviewed and describes a Women Empowerment Committee and equal-opportunity initiatives; no scoreable percentage or policy duration was extracted in this pass.",
    },
    {
        "employer_id": "5249",
        "name": "IOI Properties Group Berhad",
        "report_year": "2025",
        "report_url": "https://files.ioiproperties.com.my/dsites/s3fs-public/annual-report/file/%5BINTERACTIVE%20PDF%5D%20IOIPG%20IAR2025_06102025_0.pdf",
        "page_or_section": "Human Capital; Creating Value for Our Employees",
        "women_workforce_pct": "41",
        "women_management_pct": "41",
        "evidence_note": "FY2025 human-capital highlights report women as 41% of the total workforce and 41% of management positions.",
    },
    {
        "employer_id": "3336",
        "name": "IJM Corporation Berhad",
        "report_year": "2025",
        "report_url": "https://www.ijm.com/sites/default/files/annualreport-pdf/arc_ar_2025_1.pdf",
        "page_or_section": "Integrated Annual Report 2025, sustainability and human-capital sections",
        "evidence_note": "The official integrated annual report and its sustainability/human-capital disclosures were reviewed; no scoreable D7 fact was extracted in this pass.",
    },
    {
        "employer_id": "4677",
        "name": "YTL Corporation Berhad",
        "report_year": "2025",
        "report_url": "https://www.ytl.com/wp-content/uploads/sites/5/2025/10/YTLGroup_SR_2025.pdf",
        "page_or_section": "p. 76, Employee Benefits and Welfare / Parental Benefits",
        "flexible_remote_disclosed": "True",
        "childcare_nursing_phased_return": "True",
        "evidence_note": "The report states that certain business units offer hybrid, remote or flexible hours and that a Mother's Room provides nursing cubicles and changing facilities.",
    },
    {
        "employer_id": "6742",
        "name": "YTL Power International Berhad",
        "report_year": "2025",
        "report_url": "https://www.ytl.com/wp-content/uploads/ytles/sites/6/files/miscellaneous/YTLPI_ESG2025.pdf",
        "page_or_section": "About This Report; social performance disclosures",
        "evidence_note": "The official FY2025 ESG report was reviewed. No scoreable D7 percentage or policy-duration fact was extracted in this pass.",
    },
    {
        "employer_id": "6033",
        "name": "PETRONAS Gas Berhad",
        "report_year": "2025",
        "report_url": "https://www.petronas.com/pgb/integrated-report-2025/assets/pdf/PGB%20Sustainability%20Report%202025.pdf",
        "page_or_section": "p. 113, Talent Management / Parental Leave",
        "evidence_note": "PGB reports 120 employees taking parental leave, 119 returning, a 99% return rate and 100% retention; these metrics are retained in the note because the D7 schema has no return-rate field.",
    },
    {
        "employer_id": "5681",
        "name": "PETRONAS Dagangan Berhad",
        "report_year": "2025",
        "report_url": "https://www.mymesra.com.my/integrated-report-2025/",
        "page_or_section": "Human capital highlights",
        "women_management_pct": "39",
        "women_board_pct": "37.5",
        "evidence_note": "The 2025 integrated report reports 39% female representation on the Leadership Team and 37.5% female representation on the Board.",
    },
    {
        "employer_id": "7277",
        "name": "Dialog Group Berhad",
        "report_year": "2025",
        "report_url": "https://sr.dialogasia.com/",
        "page_or_section": "FY2025 ESG Highlights; Advancing People",
        "evidence_note": "The interactive sustainability report was reviewed and includes women-in-management and employee-assistance disclosures; no scoreable percentage or policy duration was extracted in this pass.",
    },
    {
        "employer_id": "6012",
        "name": "Maxis Berhad",
        "report_year": "2025",
        "report_url": "https://maxis.listedcompany.com/newsroom/Maxis_Integrated_Annual_Report_2025.pdf",
        "page_or_section": "p. 67, Social / employee gender breakdown",
        "women_workforce_pct": "43.0",
        "evidence_note": "Women represented 1,304 of 3,033 permanent and contract employees in 2025; 43.0% is derived from the report's disclosed counts.",
    },
    {
        "employer_id": "6947",
        "name": "CelcomDigi Berhad",
        "report_year": "2025",
        "report_url": "https://corporate.celcomdigi.com/annualreport",
        "page_or_section": "CelcomDigi Integrated Annual Report 2025",
        "evidence_note": "The official 2025 integrated annual report was located and reviewed; no scoreable D7 fact was extracted in this pass.",
    },
    {
        "employer_id": "5031",
        "name": "TIME dotCom Berhad",
        "report_year": "2025",
        "report_url": "https://www.time.com.my/wp-content/uploads/2026/04/Time-Annual-Report-2025.pdf",
        "page_or_section": "p. 55, Sustainability Statement / Talent Recruitment",
        "evidence_note": "The report discloses 41% female representation among FY2025 new hires. It is not entered as workforce representation because the denominators differ.",
    },
    {
        "employer_id": "3026",
        "name": "Dutch Lady Milk Industries Berhad",
        "report_year": "2025",
        "report_url": "https://www.dutchlady.com.my/ms/report/integrated-annual-report-2025/",
        "page_or_section": "Integrated Annual Report 2025",
        "evidence_note": "The official 2025 integrated annual report was located and reviewed; no scoreable D7 fact was extracted in this pass.",
    },
    {
        "employer_id": "3689",
        "name": "Fraser & Neave Holdings Bhd",
        "report_year": "2025",
        "report_url": "https://www.fn.com.my/investors/ar2025/",
        "page_or_section": "FY2025 ESG Scorecard; Employee Safety, Health & Well-being",
        "women_workforce_pct": "28",
        "women_management_pct": "43",
        "flexible_remote_disclosed": "True",
        "childcare_nursing_phased_return": "True",
        "evidence_note": "F&NHB reports 28% women in the workforce and 43% in managerial positions, up to two work-from-home days for eligible employees, lactation facilities and extended maternity support.",
    },
    {
        "employer_id": "4065",
        "name": "PPB Group Berhad",
        "report_year": "2025",
        "report_url": "https://www.ppbgroup.com/wp-content/uploads/ppb-sustainability-report-2025.pdf",
        "page_or_section": "pp. 20-21, Diversity, equity and inclusion / work-life integration",
        "women_workforce_pct": "29.3",
        "women_management_pct": "42",
        "flexible_remote_disclosed": "True",
        "evidence_note": "Women were 1,891 of 6,455 employees (29.3%, derived from disclosed counts), women held 42% of management roles, and flexible work arrangements were available where work situations permit.",
    },
    {
        "employer_id": "5296",
        "name": "MR D.I.Y. Group (M) Berhad",
        "report_year": "2025",
        "report_url": "https://corporate.mrdiy.com/misc/sustainability/MRDIY-Sustainability_Report_2025.pdf",
        "page_or_section": "Our People & Communities / Benefits and Entitlements",
        "maternity_days": "98",
        "paternity_days": "7",
        "evidence_note": "The FY2025 report discloses 98 days of maternity leave and seven days of paternity leave for full-time employees.",
    },
    {
        "employer_id": "5326",
        "name": "99 Speed Mart Retail Holdings Berhad",
        "report_year": "2025",
        "report_url": "https://99speedmart.com.my/wp-content/uploads/2026/04/99SMART-Integrated-Annual-Report-2025.pdf",
        "page_or_section": "p. 108, Measuring Our Progress / Diversity, Equity and Inclusion",
        "women_workforce_pct": "48.04",
        "evidence_note": "The FY2025 sustainability performance table reports 48.04% female representation in the workforce.",
    },
    {
        "employer_id": "6599",
        "name": "AEON Co. (M) Bhd",
        "report_year": "2025",
        "report_url": "https://aeongroupmalaysia.com/iar2025/assets/pdf/Download/AEON_IAR2025.pdf",
        "page_or_section": "Integrated Annual Report 2025, sustainability disclosures",
        "evidence_note": "The official integrated annual report was reviewed; no scoreable D7 fact was extracted in this pass.",
    },
    {
        "employer_id": "5878",
        "name": "KPJ Healthcare Berhad",
        "report_year": "2024",
        "report_url": "https://kpj.listedcompany.com/newsroom/KPJHB_SR_2024.pdf",
        "page_or_section": "Fostering Our People / DEI and parental leave",
        "women_workforce_pct": "78.8",
        "flexible_remote_disclosed": "True",
        "evidence_note": "Women were 13,676 of 17,352 employees (78.8%, derived from disclosed counts); KPJ also discloses flexible work arrangements and parental-leave return and retention metrics.",
    },
    {
        "employer_id": "5168",
        "name": "Hartalega Holdings Berhad",
        "report_year": "2025",
        "report_url": "https://www.insage.com.my/IR/cmn/trps02/ArTopGrid.aspx?Symbol=5168",
        "page_or_section": "Integrated Annual Report 2025; sustainability and labour-practice sections",
        "evidence_note": "The official investor-relations report listing and FY2025 integrated report were reviewed; no scoreable D7 fact was extracted in this pass.",
    },
    {
        "employer_id": "7113",
        "name": "Top Glove Corporation Bhd",
        "report_year": "2025",
        "report_url": "https://tgapp.topglove.com/IAR/2025/Sustainability_Report_2025/TG_Sustainability_Report_2025.pdf",
        "page_or_section": "Social / Work-life Integration for Employees",
        "women_management_pct": "61",
        "flexible_remote_disclosed": "True",
        "childcare_nursing_phased_return": "True",
        "evidence_note": "Top Glove reports 61% female leadership in managerial positions, flexible hours and WFH support for parents/caregivers, and nursing-room facilities.",
    },
    {
        "employer_id": "7153",
        "name": "Kossan Rubber Industries Bhd",
        "report_year": "2025",
        "report_url": "https://kossan.com.my/sustainability/",
        "page_or_section": "Sustainability Report 2025",
        "evidence_note": "The official FY2025 sustainability report was located and reviewed; no scoreable D7 fact was extracted in this pass.",
    },
    {
        "employer_id": "7106",
        "name": "Supermax Corporation Berhad",
        "report_year": "2025",
        "report_url": "https://www.supermax.com.my/media/ieqjk1as/annual-report-2025.pdf",
        "page_or_section": "p. 53, Workforce Composition and Diversity; Talent Management",
        "women_workforce_pct": "20.2",
        "flexible_remote_disclosed": "True",
        "evidence_note": "Women were 284 of 1,409 employees (20.2%, derived from disclosed counts); Supermax also states that it offers flexible working arrangements and family-friendly policies.",
    },
    {
        "employer_id": "0166",
        "name": "Inari Amertron Berhad",
        "report_year": "2025",
        "report_url": "https://www.inari-amertron.com/wp-content/uploads/2025/10/FY2025-Inari-Annual-Report-2025.pdf",
        "page_or_section": "Workplace / Employee Gender, Diversity and Inclusion",
        "women_workforce_pct": "63",
        "evidence_note": "The FY2025 report's gender-distribution chart reports women as 63% of the workforce.",
    },
    {
        "employer_id": "0097",
        "name": "ViTrox Corporation Berhad",
        "report_year": "2025",
        "report_url": "https://www.vitrox.com/pdf/investor/annual-report/vitrox_sr2025.pdf",
        "page_or_section": "p. 92, A Caring Employer / Gender Diversity; Sustainability Highlights",
        "women_workforce_pct": "32.3",
        "women_management_pct": "29.3",
        "women_board_pct": "40",
        "evidence_note": "ViTrox reports women as 32.3% of the workforce, 29.3% of managerial positions and 40% of the Board in 2025.",
    },
    {
        "employer_id": "0128",
        "name": "Frontken Corporation Berhad",
        "report_year": "2025",
        "report_url": "https://www.insage.com.my/interactiveAR/FRONTKN/interactiveAR2025/",
        "page_or_section": "pp. 23-49, Sustainability Report",
        "evidence_note": "The official 2025 annual report's sustainability section was reviewed; no scoreable D7 fact was extracted in this pass.",
    },
    {
        "employer_id": "0208",
        "name": "Greatech Technology Berhad",
        "report_year": "2025",
        "report_url": "https://www.insage.com.my/Upload/Docs/GREATEC/Greatech%20AR2025.pdf",
        "page_or_section": "pp. 37 onward, Sustainability Report",
        "evidence_note": "The official 2025 annual report's sustainability section was reviewed; no scoreable D7 fact was extracted in this pass.",
    },
    {
        "employer_id": "5292",
        "name": "UWC Berhad",
        "report_year": "2025",
        "report_url": "https://www.uwcberhad.com.my/wp-content/uploads/2026/01/Annual-Report-2025.pdf",
        "page_or_section": "p. 55, Social / Compensation and Benefits",
        "evidence_note": "UWC discloses maternity and paternity leave among permanent full-time employee benefits, but does not state exact durations in the reviewed section.",
    },
    {
        "employer_id": "5014",
        "name": "Malaysia Airports Holdings Berhad",
        "report_year": "2023",
        "report_url": "https://corporate.malaysiaairports.com.my/en/about-us/reports/annual-report",
        "page_or_section": "Annual Report 2023 and report archive",
        "evidence_note": "The official report archive was reviewed using the latest annual report listed there; no scoreable D7 fact was extracted in this pass.",
    },
    {
        "employer_id": "3182",
        "name": "Genting Berhad",
        "report_year": "2025",
        "report_url": "https://www.genting.com/sustainability-reports",
        "page_or_section": "Sustainability Report 2025; Enhancing Workplace Practices",
        "flexible_remote_disclosed": "True",
        "evidence_note": "Genting's workplace-practice disclosure states that flexible work arrangements are implemented where appropriate to manage workload and excessive-hours risk.",
    },
]


REPORT_COLUMNS = [
    "employer_id",
    "name",
    "report_year",
    "report_url",
    "page_or_section",
    "women_workforce_pct",
    "women_management_pct",
    "women_board_pct",
    "maternity_days",
    "paternity_days",
    "flexible_remote_disclosed",
    "childcare_nursing_phased_return",
    "evidence_note",
    "recognition_note",
    "extraction_status",
]


def normalize_report(row: dict[str, str]) -> dict[str, str]:
    normalized = {column: "" for column in REPORT_COLUMNS}
    normalized.update(row)
    normalized["extraction_status"] = "source_confirmed_manual_review"
    return normalized


def write_csv(path: Path, data: pd.DataFrame) -> None:
    data.to_csv(path, index=False, encoding="utf-8")


def main() -> None:
    old_path = EMP / "D7_report_evidence_20.csv"
    new_path = EMP / "D7_report_evidence_50.csv"
    ARCHIVE.mkdir(exist_ok=True)
    archive_path = ARCHIVE / "D7_report_evidence_initial20_2026-08-27.csv"
    if old_path.exists() and not archive_path.exists():
        shutil.copy2(old_path, archive_path)

    seed_path = old_path if old_path.exists() else archive_path
    reports = pd.read_csv(seed_path, dtype=str).fillna("")
    additions = pd.DataFrame([normalize_report(row) for row in NEW_REPORTS], columns=REPORT_COLUMNS)
    reports = pd.concat([reports[REPORT_COLUMNS], additions], ignore_index=True)
    reports = reports.drop_duplicates("employer_id", keep="last")
    reports = reports.sort_values("employer_id", key=lambda s: pd.to_numeric(s, errors="coerce")).reset_index(drop=True)
    assert len(reports) == 50 and reports["employer_id"].nunique() == 50
    write_csv(new_path, reports)
    if old_path.exists():
        old_path.unlink()

    field_meta = {
        "women_workforce_pct": ("gender_equity", "%"),
        "women_management_pct": ("gender_equity", "%"),
        "women_board_pct": ("gender_equity", "%"),
        "maternity_days": ("policy_flex", "days"),
        "paternity_days": ("policy_flex", "days"),
        "flexible_remote_disclosed": ("policy_flex", "boolean"),
        "childcare_nursing_phased_return": ("policy_flex", "boolean"),
    }
    atomic: list[dict[str, str]] = []
    for source in reports.to_dict("records"):
        for field, (pillar, unit) in field_meta.items():
            value = source[field]
            if value == "":
                continue
            atomic.append(
                {
                    "evidence_id": f"EV{len(atomic) + 1:04d}",
                    "employer_id": source["employer_id"],
                    "employer_name": source["name"],
                    "pillar": pillar,
                    "fact_field": field,
                    "extracted_value": value,
                    "unit": unit,
                    "source_year": source["report_year"],
                    "source_url": source["report_url"],
                    "page_or_section": source["page_or_section"],
                    "evidence_paraphrase": source["evidence_note"],
                    "verification_status": "source_confirmed_pending_second_reviewer",
                    "reviewer": "",
                    "review_date": "",
                }
            )
        if source["recognition_note"]:
            atomic.append(
                {
                    "evidence_id": f"EV{len(atomic) + 1:04d}",
                    "employer_id": source["employer_id"],
                    "employer_name": source["name"],
                    "pillar": "recognition",
                    "fact_field": "recognition_note",
                    "extracted_value": source["recognition_note"],
                    "unit": "text",
                    "source_year": source["report_year"],
                    "source_url": source["report_url"],
                    "page_or_section": source["page_or_section"],
                    "evidence_paraphrase": source["recognition_note"],
                    "verification_status": "source_confirmed_pending_second_reviewer",
                    "reviewer": "",
                    "review_date": "",
                }
            )
    atomic_df = pd.DataFrame(atomic)
    write_csv(EMP / "D7_evidence_lineage.csv", atomic_df)

    search = pd.read_csv(EMP / "D7_report_search_audit_50.csv", dtype=str).fillna("")
    universe = pd.read_csv(EMP / "D7_employer_universe_50.csv", dtype=str).fillna("")
    queue = pd.read_csv(EMP / "D7_manual_validation_queue_50.csv", dtype=str).fillna("")
    report_by_id = reports.set_index("employer_id").to_dict("index")

    for idx, row in search.iterrows():
        report = report_by_id[row["employer_id"]]
        search.loc[idx, ["search_status", "has_report", "report_year", "report_url", "no_report_zero_rule_applied", "search_completion_note"]] = [
            "report_located_and_reviewed",
            "True",
            report["report_year"],
            report["report_url"],
            "False",
            "Official sustainability, integrated or annual report located and reviewed; any extracted facts remain pending independent second review.",
        ]
    assert search["search_status"].eq("report_located_and_reviewed").all()
    write_csv(EMP / "D7_report_search_audit_50.csv", search)

    for idx, row in universe.iterrows():
        report = report_by_id[row["employer_id"]]
        universe.loc[idx, ["has_report", "report_year", "report_url", "score_status", "evidence_status"]] = [
            "True",
            report["report_year"],
            report["report_url"],
            "blocked_incomplete_evidence",
            "pending_second_reviewer",
        ]
        if not row["confidence"] or "recognition only" in row["confidence"].lower():
            universe.loc[idx, "confidence"] = "Low - partial report disclosure"
    write_csv(EMP / "D7_employer_universe_50.csv", universe)

    queue["priority"] = "normal"
    queue["review_status"] = "evidence_second_review_pending"
    queue["checks_required"] = "Verify official URL/year, page or section locator, normalized facts, recognition status and deterministic scores; do not approve production scoring until complete."
    write_csv(EMP / "D7_manual_validation_queue_50.csv", queue)

    lineage_path = DMP / "D10_data_lineage.csv"
    lineage = pd.read_csv(lineage_path, dtype=str).fillna("")
    mask = lineage["deliverable"].eq("D7")
    lineage.loc[mask, "source"] = "50-company Bursa candidate list; 50 reviewed official sustainability/integrated/annual reports; separate official recognition evidence"
    lineage.loc[mask, "transform"] = "Two-stage official report search; atomic extraction; deterministic scoring controls; independent second-review queue"
    lineage.loc[mask, "output"] = "D7_employer_universe_50.csv; D7_report_evidence_50.csv; D7_evidence_lineage.csv; D7_report_search_audit_50.csv"
    write_csv(lineage_path, lineage)

    print(
        {
            "reports": len(reports),
            "reviewed_searches": int(search["search_status"].eq("report_located_and_reviewed").sum()),
            "atomic_facts": len(atomic_df),
            "second_review_pending": int(queue["review_status"].eq("evidence_second_review_pending").sum()),
            "archived_seed": str(archive_path.relative_to(ROOT)),
        }
    )


if __name__ == "__main__":
    main()
