"""Validate and inspect Toolmux seed datasets. This module never installs tools."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1] / 'seeds' / 'tools'
ALLOWED_METHODS={'apt','git'}
ALLOWED_STATUS={'verified','experimental','root-required','proot-required','legacy','unverified'}

def load_records(root: Path=ROOT):
    out=[]
    for path in sorted(root.glob('*.json')):
        rows=json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(rows,list): raise ValueError(f'{path.name}: dataset must be a list')
        for row in rows: out.append((path,row))
    return out

def validate_record(row):
    errors=[]
    slug=row.get('slug','')
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',slug): errors.append('invalid slug')
    if not str(row.get('name','')).strip(): errors.append('missing name')
    if not str(row.get('category','')).strip(): errors.append('missing category')
    repo=row.get('repository',''); p=urlparse(repo)
    if p.scheme not in {'http','https'} or not p.netloc: errors.append('invalid repository URL')
    install=row.get('install') or {}; method=install.get('method')
    if method not in ALLOWED_METHODS: errors.append('unsupported install method')
    deps=install.get('dependencies',[])
    if not isinstance(deps,list) or any(not isinstance(x,str) or not x.strip() for x in deps): errors.append('invalid dependencies')
    if method=='apt' and not install.get('package_name'): errors.append('apt requires package_name')
    if method=='git' and (not install.get('repository_name') or not install.get('repository_url')): errors.append('git requires repository_name/repository_url')
    status=(row.get('termux') or {}).get('status','unverified')
    if status not in ALLOWED_STATUS: errors.append('invalid compatibility status')
    return errors

def validate_dataset(root: Path=ROOT, category=None, limit=None):
    rows=load_records(root); seen=set(); result=[]; errors=[]
    for path,row in rows:
        if category and row.get('category')!=category and path.stem!=category: continue
        slug=row.get('slug')
        if slug in seen: errors.append(f'{path.name}:{slug}: duplicate slug')
        seen.add(slug)
        for err in validate_record(row): errors.append(f'{path.name}:{slug or "?"}: {err}')
        result.append(row)
        if limit and len(result)>=limit: break
    return result,errors

def main(argv=None):
    ap=argparse.ArgumentParser(description='Validate Toolmux catalog seed datasets')
    ap.add_argument('--validate',action='store_true'); ap.add_argument('--category'); ap.add_argument('--limit',type=int)
    ap.add_argument('--dataset',type=Path,default=ROOT)
    args=ap.parse_args(argv)
    rows,errors=validate_dataset(args.dataset,args.category,args.limit)
    print(f'Toolmux Seed Dataset\nLoaded: {len(rows)}\nValid: {len(rows)-len({e.split(":",2)[1] for e in errors if ":" in e})}\nErrors: {len(errors)}')
    for e in errors: print('ERROR',e)
    return 1 if errors else 0
if __name__=='__main__': raise SystemExit(main())
