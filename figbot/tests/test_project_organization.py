import hashlib,json,zipfile
from pathlib import Path
from scripts.project_paths import ROOT,CURRENT,PRINTS,CAD,SHOPPING,ARCHIVE

def test_stable_generators_and_paths():
    from cad.prototype_arm import build_linka_v1 as a
    from scripts import package_linka_plates as p,build_linka_shopping as s
    assert a.OUT==CAD and p.OUT==PRINTS and p.SOURCE==CAD
    assert s.OUT==SHOPPING/'VERI'
    assert not list((ROOT/'releases').glob('LINKA*'))
    assert not (ROOT/'cad/prototype_arm/linka_v1').exists()
    assert {p.name for p in CURRENT.iterdir() if p.is_dir()}=={'BASKI','CAD','ALISVERIS','YAZILIM'}

def test_all_archived_originals_match_verified_manifest():
    report=json.loads((ROOT/'reports/project_organization/ARCHIVE_MANIFEST.json').read_text(encoding='utf-8'))
    assert report['status']=='ZIP_SHA256_VERIFIED'
    with zipfile.ZipFile(ARCHIVE) as z:
        assert len(z.namelist())==len(set(z.namelist()))
        for row in report['files']:
            assert hashlib.sha256(z.read(row['path'])).hexdigest()==row['sha256'],row['path']

def test_migration_does_not_change_any_current_part_geometry():
    rows=json.loads((ROOT/'reports/linka_cable_exit_audit/COMPARISON_TO_L12.json').read_text())
    assert len(rows)==22
    for row in rows:
        from scripts.publish_twin_scoop import RETIRED
        if row['part'] in RETIRED:
            assert not (CAD/'PRINT_STL'/(row['part']+'.stl')).exists()
            continue
        if row['part']=='L1-15-COUPLER':
            status=json.loads((CAD/'CUBUK_MAFSALI/STATUS.json').read_text())
            assert status['revision']=='DEC-085'
            assert hashlib.sha256((CAD/'PRINT_STL/L1-15-COUPLER.stl').read_bytes()).hexdigest()==status['geometry_sha256']['L1-15-COUPLER']
            continue
        assert hashlib.sha256((CAD/'PRINT_STL'/(row['part']+'.stl')).read_bytes()).hexdigest().upper()==row['new_sha']

def test_live_manifest_and_local_navigation():
    rows=json.loads((CURRENT/'DOSYA_LISTESI.json').read_text())
    for row in rows:
        p=CURRENT/row['path']
        assert p.is_file() and p.stat().st_size==row['bytes']
        assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
    page=(ROOT/'viewer/kol.html').read_text(encoding='utf-8')
    assert '/models/guncel/' in page and '/models/linka-v1/' not in page
    for name in ['index.html','forma-v6.html','linka-v1.html']:
        assert 'url=/kol.html' in (ROOT/'viewer'/name).read_text(encoding='utf-8')
    for name in ['ASSEMBLY','BASE','GRIPPER','PICKUP','RELEASE']:
        assert (ROOT/'viewer/public/models/guncel'/('LINKA_L1_'+name+'.glb')).is_file()
