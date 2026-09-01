"""Create a checked dataset archive; excludes caches and all live/private DB content."""
from pathlib import Path
import hashlib
import json
import zipfile

root = Path(__file__).resolve().parent
checks = json.loads((root / '02_QA/regression_results.json').read_text())
assert checks['status'] == 'PASS' and checks['tests_run'] == 12
files = sorted(p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts
               and p.name not in ('.DS_Store', 'SHA256SUMS.txt'))
lines = [hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + str(p.relative_to(root)) for p in files]
(root / 'SHA256SUMS.txt').write_text('\n'.join(lines) + '\n')
files.append(root / 'SHA256SUMS.txt')
archive = root.with_suffix('.zip')
with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as bundle:
    for path in files:
        bundle.write(path, arcname=str(Path(root.name) / path.relative_to(root)))
with zipfile.ZipFile(archive) as bundle:
    assert bundle.testzip() is None
    assert len(bundle.namelist()) == len(files)
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
archive.with_suffix('.zip.sha256').write_text(digest + '  ' + archive.name + '\n')
print(json.dumps({'archive': str(archive), 'files': len(files), 'bytes': archive.stat().st_size,
                  'sha256': digest, 'zip_integrity': 'PASS'}, indent=2))
