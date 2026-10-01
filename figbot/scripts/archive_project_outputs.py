"""Explicit output inventory; archive and SHA256 verification precede cleanup.

No source tree, git data, environment or original external references is removed.
Each original is removed only after a closed ZIP has been read back and both
archive and unchanged source hashes verified; bounded batches limit disk usage.
"""
import hashlib,json,zipfile,shutil
from pathlib import Path
from scripts.project_paths import ROOT,ARCHIVE

REPORT=ROOT/'reports/project_organization'

def targets():
    result=list((ROOT/'releases').iterdir())
    result += [p for p in (ROOT/'cad/prototype_arm').iterdir() if p.is_dir() and p.name!='__pycache__']
    result += [p for p in (ROOT/'viewer/public/models').iterdir() if p.name!='guncel']
    result += [p for p in (ROOT/'viewer').glob('*.html') if p.name!='kol.html']
    result += [ROOT/'outputs',ROOT/'output',ROOT/'purchasing/LINKA_L1_20260914']
    result += [p for p in (ROOT/'renders').glob('*') if p.is_file()]
    result += [REPORT/'INCOMPLETE_COPY']
    return sorted(set(p.resolve() for p in result if p.exists()))

def main():
    if ARCHIVE.exists():raise RuntimeError('Archive already exists; do not overwrite history.')
    REPORT.mkdir(parents=True,exist_ok=True);ARCHIVE.parent.mkdir(exist_ok=True)
    selected=targets();rows=[]
    (REPORT/'TARGETS.json').write_text(json.dumps([str(p) for p in selected],indent=2))
    for p in selected:
        p.relative_to(ROOT.resolve())
        if p.is_symlink():raise RuntimeError('Symlink target refused: '+str(p))
        files=[]
        for f in ([p] if p.is_file() else sorted(p.rglob('*'))):
            if f.is_symlink():raise RuntimeError('Symlink file refused: '+str(f))
            if f.is_file():files.append(f)
        required=sum(f.stat().st_size for f in files)+32*1024*1024
        if shutil.disk_usage(ROOT).free < required:raise RuntimeError('Insufficient staging space for '+str(p))
        batch=[]
        with zipfile.ZipFile(ARCHIVE,'a',allowZip64=True) as z:
            for f in files:
                rel=f.relative_to(ROOT).as_posix();data=f.read_bytes()
                digest=hashlib.sha256(data).hexdigest()
                kind=zipfile.ZIP_STORED if f.suffix.lower() in ['.apk','.zip','.png','.jpg','.pdf','.3mf'] else zipfile.ZIP_DEFLATED
                z.writestr(rel,data,compress_type=kind,compresslevel=1 if kind==zipfile.ZIP_DEFLATED else None)
                batch.append({'path':rel,'bytes':len(data),'sha256':digest})
        with zipfile.ZipFile(ARCHIVE) as z:
            for row in batch:
                if hashlib.sha256(z.read(row['path'])).hexdigest()!=row['sha256']:raise RuntimeError(row['path'])
                if hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest()!=row['sha256']:raise RuntimeError('Source changed: '+row['path'])
        # Authorized archive-and-remove: final absolute target checked again,
        # no symlinks, source hashes unchanged, closed ZIP read back successfully.
        resolved=p.resolve();resolved.relative_to(ROOT.resolve())
        if resolved!=p or resolved not in selected:raise RuntimeError('Target changed')
        if p.is_dir():shutil.rmtree(p)
        else:p.unlink()
        rows.extend(batch)
        (REPORT/'ARCHIVE_PROGRESS.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
        print(f'Verified and archived: {p.relative_to(ROOT)} ({len(batch)} files)',flush=True)
    with zipfile.ZipFile(ARCHIVE,'a') as z:z.writestr('_ARCHIVE_MANIFEST.json',json.dumps(rows,indent=2))
    manifest={'status':'ZIP_SHA256_VERIFIED','archive':str(ARCHIVE),'files':rows,'remove_targets':[str(p) for p in selected]}
    (REPORT/'ARCHIVE_MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps({'verified_files':len(rows),'source_bytes':sum(r['bytes'] for r in rows),'zip_bytes':ARCHIVE.stat().st_size}),flush=True)

if __name__=='__main__':main()
