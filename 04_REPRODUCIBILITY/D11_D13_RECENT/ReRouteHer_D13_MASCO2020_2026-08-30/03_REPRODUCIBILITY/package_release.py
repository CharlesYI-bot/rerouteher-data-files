"""Archive validated outputs and checksums without local working caches."""
import hashlib,json,zipfile
from common import ROOT,sha

def main():
    report=json.loads((ROOT/'02_QA/D13_validation_report.json').read_text())
    assert report['result']=='PASS'
    workbook=ROOT.parent/'outputs/01a047e7-ceba-7df3-8d1a-ba8071e66430/D13_MASCO2020_TitleCase_Review.xlsx'
    omit_dirs={'node_modules','__pycache__','previews'}
    omit_names={'table_payloads.json','candidate_review.json','retrieval_vectors.npz','file_checksums.sha256','package_report.json'}
    files=[]
    for p in sorted(ROOT.rglob('*')):
        rel=p.relative_to(ROOT)
        if p.is_file() and not p.is_symlink() and not set(rel.parts)&omit_dirs and p.name not in omit_names:files.append((p,str(rel)))
    files.append((workbook,'06_REVIEW/D13_MASCO2020_TitleCase_Review.xlsx'))
    checksums=ROOT/'file_checksums.sha256';checksums.write_text(''.join(sha(p)+'  '+rel+'\n' for p,rel in files))
    files.append((checksums,checksums.name))
    target=ROOT.parent/(ROOT.name+'.zip');temp=target.with_suffix('.zip.tmp')
    with zipfile.ZipFile(temp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p,rel in files:z.write(p,ROOT.name+'/'+rel)
    with zipfile.ZipFile(temp) as z:
        assert z.testzip() is None
        for p,rel in files:assert hashlib.sha256(z.read(ROOT.name+'/'+rel)).hexdigest()==sha(p),rel
    temp.replace(target)
    result={'archive':str(target),'files':len(files),'bytes':target.stat().st_size,'sha256':sha(target),
        'integrity':'PASS','all_archived_file_checksums_verified':True,'validation_checks_passed':report['checks_passed']}
    (ROOT/'02_QA/package_report.json').write_text(json.dumps(result,indent=2)+'\n')
    target.with_suffix('.zip.sha256').write_text(result['sha256']+'  '+target.name+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
