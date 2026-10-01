"""Stable delivery paths; revisions belong in metadata, never directory names."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CURRENT=ROOT/'GUNCEL'
PRINTS=CURRENT/'BASKI'
CAD=CURRENT/'CAD'
SHOPPING=CURRENT/'ALISVERIS'
SOFTWARE=CURRENT/'YAZILIM'
ARCHIVE=ROOT/'ARSIV/ESKI_SURUMLER.zip'

def read_original(path):
    """Read an audited historical file in place or at its original path in ZIP."""
    import zipfile
    p=Path(path).resolve()
    rel=p.relative_to(ROOT.resolve()).as_posix()
    if p.is_file():return p.read_bytes()
    with zipfile.ZipFile(ARCHIVE) as z:return z.read(rel)
