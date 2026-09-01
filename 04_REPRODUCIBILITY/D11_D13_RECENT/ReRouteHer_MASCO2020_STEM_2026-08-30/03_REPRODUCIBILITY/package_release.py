"""Package validated deliverables without dependency links or raw PDF text."""
from pathlib import Path
import hashlib,json,zipfile

ROOT=Path(__file__).resolve().parents[1]
WORKBOOK=ROOT.parent/'outputs/01a047e7-ceba-7df3-8d1a-ba8071e66430/MASCO2020_STEM_Review.xlsx'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def package():
    report=json.loads((ROOT/'02_QA/validation_report.json').read_text())
    assert report['result']=='PASS' and report['checks_passed']==43
    omit_dirs={'node_modules','__pycache__','previews'}
    omit_files={'table_payloads.json','masco2020_pdf_pages.json','file_checksums.sha256','package_report.json'}
    files=[]
    for p in sorted(ROOT.rglob('*')):
        rel=p.relative_to(ROOT)
        if not p.is_file() or p.is_symlink() or set(rel.parts)&omit_dirs or p.name in omit_files:continue
        files.append((p,str(rel)))
    files.append((WORKBOOK,'06_REVIEW/MASCO2020_STEM_Review.xlsx'))
    checksums=ROOT/'file_checksums.sha256'
    checksums.write_text(''.join(digest(p)+'  '+rel+'\n' for p,rel in files))
    files.append((checksums,checksums.name))
    output=ROOT.parent/(ROOT.name+'.zip')
    temp=output.with_suffix('.zip.tmp')
    with zipfile.ZipFile(temp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p,rel in files:z.write(p,ROOT.name+'/'+rel)
    with zipfile.ZipFile(temp) as z:
        assert z.testzip() is None
        assert len(z.namelist())==len(files)
        assert all('node_modules' not in p and 'masco2020_pdf_pages' not in p for p in z.namelist())
        for p,rel in files:
            assert hashlib.sha256(z.read(ROOT.name+'/'+rel)).hexdigest()==digest(p),rel
    temp.replace(output)
    result={'archive':str(output),'files':len(files),'bytes':output.stat().st_size,
            'sha256':digest(output),'integrity':'PASS','every_archived_file_checksum_verified':True,
            'omitted':'Dependency symlinks, preview images and large intermediate matrices/full-PDF-text cache.'}
    (ROOT/'02_QA/package_report.json').write_text(json.dumps(result,indent=2)+'\n')
    output.with_suffix('.zip.sha256').write_text(result['sha256']+'  '+output.name+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':package()
