"""Bounded live application evaluation; no training, database or code writes.

Original PDFs are read-only. Persist only test metadata and filtered responses;
CV raw text and experience descriptions stay in memory during a request chain.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from pypdf import PdfReader

OUT = Path(__file__).resolve().parent
SOURCE = Path('/Users/charlesyi/Downloads/archive 3/data/data')
BASE = 'https://rerouteher.curl.my'
SEED = 'rerouteher-20260830-v1'
QUOTAS = {
    'INFORMATION-TECHNOLOGY': 5, 'ENGINEERING': 4, 'TEACHER': 3,
    'HEALTHCARE': 2, 'DESIGNER': 2, 'AGRICULTURE': 1, 'AUTOMOBILE': 1,
    'AVIATION': 1, 'DIGITAL-MEDIA': 1, 'CONSTRUCTION': 1, 'FINANCE': 1,
    'HR': 1, 'SALES': 1, 'CHEF': 1,
}


def save(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n')


def scrub(value):
    if not value:
        return value
    value = re.sub(r'\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b', '[EMAIL]', value)
    value = re.sub(r'(?<!\w)\+?\d[\d ().-]{7,}\d(?!\w)', '[NUMBER]', value)
    value = re.sub(r'Marilyn\s+Hunter', '[PERSON]', value, flags=re.I)
    return value


def prepare():
    files = sorted(SOURCE.rglob('*.pdf'))
    counts = Counter(p.parent.name for p in files)
    selected, hashes = [], set()
    for category, count in QUOTAS.items():
        candidates = sorted((p for p in files if p.parent.name == category),
                            key=lambda p: hashlib.sha256((SEED + str(p.relative_to(SOURCE))).encode()).hexdigest())
        for p in candidates:
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
            if digest in hashes:
                continue
            reader = PdfReader(p)
            text = '\n'.join(page.extract_text() or '' for page in reader.pages)
            lines = [s.strip() for s in text.splitlines() if s.strip()]
            row = dict(case_id=f'T{len(selected)+1:02}', category=category,
                       file=str(p.relative_to(SOURCE)), sha256=digest,
                       bytes=p.stat().st_size, pages=len(reader.pages),
                       text_characters=len(text), headline=scrub(lines[0])[:160] if lines else '')
            selected.append(row)
            hashes.add(digest)
            count -= 1
            if not count:
                break
        assert count == 0, category
    assert len(selected) == len(hashes) == 25
    save(OUT / 'sample_manifest.json', dict(source=str(SOURCE), seed=SEED,
         selection='Deterministic SHA256-ranked stratified sample; selected PDF hashes are unique.',
         population_count=len(files), population_categories=dict(sorted(counts.items())),
         quotas=QUOTAS, cases=selected))
    print(json.dumps(selected, indent=2))


def post(endpoint, payload=None, pdf=None):
    if pdf:
        boundary = 'ReRouteHerVerification20260830'
        body = (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{pdf.name}"\r\n'
                'Content-Type: application/pdf\r\n\r\n').encode() + pdf.read_bytes() + f'\r\n--{boundary}--\r\n'.encode()
        content_type = f'multipart/form-data; boundary={boundary}'
    else:
        body = json.dumps(payload).encode()
        content_type = 'application/json'
    req = urllib.request.Request(BASE + endpoint, data=body, headers={
        'Content-Type': content_type, 'User-Agent': 'ReRouteHer-25Resume-Verification/1.0'})
    start = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            return {'status': response.status, 'seconds': round(time.monotonic()-start, 3)}, json.load(response)
    except urllib.error.HTTPError as e:
        # Do not retain response text that may echo submitted resume content.
        return {'status': e.code, 'seconds': round(time.monotonic()-start, 3)}, None
    except (urllib.error.URLError, TimeoutError) as e:
        return {'status': 'transport_error', 'error_type': type(e).__name__,
                'seconds': round(time.monotonic()-start, 3)}, None


def run(limit=None):
    manifest = json.loads((OUT / 'sample_manifest.json').read_text())
    results_file = OUT / 'live_results.json'
    results = json.loads(results_file.read_text()) if results_file.exists() else dict(
        started_utc=datetime.now(timezone.utc).isoformat(), base_url=BASE,
        method='Sequential PDF parse -> unedited parsed CV snapshot -> gap for each recommended role.',
        break_input={'duration_years': 2, 'activities': []}, cases=[])
    done = {r['case_id'] for r in results['cases']}
    pending = [r for r in manifest['cases'] if r['case_id'] not in done]
    if limit:
        pending = pending[:limit]
    for row in pending:
        result = {'case_id': row['case_id'], 'category': row['category'], 'file': row['file']}
        pdf = SOURCE / row['file']
        assert hashlib.sha256(pdf.read_bytes()).hexdigest() == row['sha256']
        result['parse_http'], parsed = post('/api/cv/parse', pdf=pdf)
        if parsed and 'cv' in parsed:
            cv = parsed['cv']
            result['parsed'] = {'raw_text_characters': len(cv.get('raw_text', '')),
                'experience_count': len(cv.get('experiences', [])),
                'titles': [scrub(e.get('title')) for e in cv.get('experiences', [])],
                'skill_mentions': cv.get('skill_mentions', [])}
            result['snapshot_http'], snap = post('/api/snapshot/generate',
                payload={'cv': cv, 'break': results['break_input']})
            if snap and 'recommended_roles' in snap:
                result['snapshot'] = snap
                skills = [{k: s[k] for k in ('skill', 'skill_id', 'source') if k in s}
                          for s in snap.get('professional_skills', []) + snap.get('reframed_skills', [])]
                result['gaps'] = []
                for role in snap['recommended_roles']:
                    http, gap = post('/api/gap/compute', payload={'skills': skills, 'target_role': role['role']})
                    result['gaps'].append({'target_role': role['role'], 'http': http, 'result': gap})
        results['cases'].append(result)
        results['last_updated_utc'] = datetime.now(timezone.utc).isoformat()
        save(results_file, results)
        snap = result.get('snapshot', {})
        print(json.dumps({'case': row['case_id'], 'category': row['category'],
            'parse': result['parse_http'], 'titles': result.get('parsed', {}).get('titles'),
            'snapshot': result.get('snapshot_http'), 'previous': snap.get('previous_occupation'),
            'skills': len(snap.get('professional_skills', [])),
            'gaps': [{'role': g['target_role'], 'status': g['http']['status'],
                      'readiness': (g['result'] or {}).get('readiness'),
                      'matches': len((g['result'] or {}).get('skills_have', []))}
                     for g in result.get('gaps', [])]}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['prepare', 'run'])
    parser.add_argument('--limit', type=int)
    args = parser.parse_args()
    prepare() if args.command == 'prepare' else run(args.limit)
