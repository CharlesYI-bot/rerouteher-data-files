from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "00_SOURCE_ARCHIVE" / "ESCO_to_ONET-SOC_official.xlsx"
cw = pd.read_excel(path, sheet_name=0, header=3, dtype=str)
codes = ["2512", "2511", "2423", "2431", "2643", "2166", "4311", "4222", "4120", "2359"]
for code in codes:
    rows = cw[cw["ESCO/ISCO Code"].str.startswith(code + ".", na=False)]
    print(f"\n### {code}: {len(rows)} mappings")
    print(rows.head(30).to_string(index=False))
