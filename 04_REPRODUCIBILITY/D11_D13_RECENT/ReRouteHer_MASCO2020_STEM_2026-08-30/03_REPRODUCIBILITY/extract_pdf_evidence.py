"""Cache page text for source checks without modifying the official PDF."""
from pathlib import Path
import json
from pypdf import PdfReader

root=Path(__file__).resolve().parents[1]
pdf=root.parent/'MASCO_remote_work/input/masco/2020/en/MASCO_2020_English_official.pdf'
out=root/'02_QA/masco2020_pdf_pages.json'
if not out.exists():
    reader=PdfReader(pdf)
    pages=[p.extract_text() or '' for p in reader.pages]
    out.write_text(json.dumps(pages,ensure_ascii=False))
    print(f'Cached {len(pages)} official source pages')
else:print('Using existing page cache')
