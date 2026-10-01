"""DEC-086 publication, invoked through publish_current; snapshot before install."""
import json,csv,shutil,hashlib
from collections import Counter
import trimesh
from scripts.project_paths import ROOT,CURRENT,CAD,PRINTS

RETIRED={'L1-16-PALM','L1-17-FINGER','L1-18-PAD','L1-19-SPOOL','L1-25-FINGER-BUSH'}

def install():
    from scripts.publish_current import snapshot_before_rebuild
    stage=ROOT/'.codex_artifacts/twin_scoop_build'
    assert json.loads((stage/'STATUS.json').read_text())['revision']=='DEC-086'
    old=json.loads((CAD/'TUTUCU/MASS_AND_PARTS.json').read_text())
    snapshot_before_rebuild()
    # The verified snapshot contains every removed path. Stay within current CAD.
    targets=[CAD/'TUTUCU',CAD/'DISLI_TUTUCU_INCELEME',CAD/'URDF',CAD/'VIEWS']
    targets+=list(CAD.glob('*TRIPOD*'))
    for folder in ['PART_STEP','PRINT_STL','3MF']:
        targets+=[f for f in (CAD/folder).iterdir() if f.stem in RETIRED]
    for p in targets:
        assert p.resolve().is_relative_to(CAD.resolve()) and p.resolve()!=CAD.resolve()
        if p.is_dir():shutil.rmtree(p)
        elif p.exists():p.unlink()
    shutil.copytree(stage,CAD/'TUTUCU')
    shutil.copytree(stage/'ARM_REVIEW/URDF',CAD/'URDF')
    (CAD/'VIEWS').mkdir(exist_ok=True)
    for f in stage.glob('*.png'):shutil.copy2(f,CAD/'VIEWS'/f.name)
    for src,dst in [('TWIN_ARM','ASSEMBLY'),('TWIN_OPEN','GRIPPER'),('TWIN_CLOSED','GRIPPER_CLOSED'),('BASE','BASE'),('PICKUP','PICKUP'),('RELEASE','RELEASE')]:
        for ext in ['glb','step']:shutil.copy2(stage/f'LINKA_L1_{src}.{ext}',CAD/f'LINKA_L1_{dst}.{ext}')
    for f in stage.glob('*.glb'):shutil.copy2(f,CAD/f.name)
    for folder,target in [('PART_STEP','PART_STEP'),('PROTOTIP_STL','PRINT_STL'),('3MF','3MF')]:
        for f in (stage/folder).iterdir():shutil.copy2(f,CAD/target/f.name)
    shutil.copy2(stage/'MASS_AND_PARTS.json',CAD/'MASS_AND_PARTS.json')
    new=json.loads((stage/'MASS_AND_PARTS.json').read_text())
    def load(d):
        rows=[r for r in d['rows'] if r['frame']=='tool']
        return dict(mass_g=sum(r['mass_g'] for r in rows),horizontal_wrist_self_weight_nm=sum(r['mass_g']*r['center_mm'][0] for r in rows)*9.81e-6)
    comparison=dict(previous=load(old),current=load(new),basis='CAD solid/assigned component masses; horizontal local X, gravity -Z. No wiring, no dynamic/friction allowance.',fruit_50g_at_center_nm=.05*9.81*.099,torque_approval=False)
    (CAD/'TUTUCU/MASS_COMPARISON.json').write_text(json.dumps(comparison,indent=2))
    # Historical rod geometry stays active; its old full-arm view is superseded.
    shutil.copy2(stage/'TWIN_ARM.png',CAD/'CUBUK_MAFSALI/YENI_CUBUK_KOL.png')
    shutil.copy2(stage/'MASS_AND_PARTS.json',CAD/'CUBUK_MAFSALI/MASS_AND_PARTS.json')
    (CAD/'ASSEMBLY_NOTES_TR.md').write_text('# DEC-086\n\nGüncel tutucu ve taban kapağı: TUTUCU/OKU.md. Çubuk değişmedi: CUBUK_MAFSALI/MONTAJ.md.07/08/10 yeni baskılardır. Fiziksel dayanım, servo torku ve taban gerçek yıldız oturması doğrulanmadı.\n',encoding='utf-8')
    (CAD/'PLASTIK_BURC_MONTAJI.md').write_text('# Güncel plastik burçlar\n\nDirsek L1-23/24:06 tablası. Çubuk L1-26:09 tablası. Pasif kepçe TS-BUSH:07 tablası. Eski L1-25 parmak burcu kullanılmaz. Tutucu montajı TUTUCU/OKU.md. Metal vidalar burcun içinden geçer; plastik vida değildir. Sıkıldığında dönen parça serbest kalmalı; fiziksel sıkma/sünme deneyi gerekli.\n',encoding='utf-8')
    for stale in ['VALIDATION.json','TEST_RESULTS.txt']:
        (CAD/stale).write_text('DEC-086 validation pending; previous evidence archived.\n')

def refresh():
    from scripts.publish_current import run,digest
    run('scripts.package_twin_plates')
    run('scripts.qa_tripod_plates')
    run('scripts.build_linka_shopping')
    run('scripts.build_hardware_counter_list')
    manifest=json.loads((PRINTS/'TABLA_LISTESI.json').read_text())
    counts=Counter(e['id'] for p in manifest['plates'] for e in p['instances'])
    rows=[]
    for pid,n in counts.items():
        m=trimesh.load_mesh(CAD/'PRINT_STL'/f'{pid}.stl')
        rows.append(dict(id=pid,count=n,material='PLA',cad_mass_each_g=m.volume*.00124))
    with (CAD/'PRINT_BOM.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['id','count','material','cad_mass_each_g']);w.writeheader();w.writerows(rows)
    cost=dict(revision='DEC-086',printed_part_instances=sum(counts.values()),cad_solid_mass_g=sum(r['count']*r['cad_mass_each_g'] for r in rows),filament_price_per_kg=None,hardware_total=None,total=None,status='PRICING INCOMPLETE; no purchase',note='CAD solid volume only; supports/wiring/actual filament price unknown. Partial historic hardware estimate: ALISVERIS/VERI/MALIYET.json.')
    (CAD/'COST_ESTIMATE.json').write_text(json.dumps(cost,indent=2))
    status=dict(revision='DEC-086',current_directory='GUNCEL',print_directory='GUNCEL/BASKI',cad_directory='GUNCEL/CAD',viewer_url='http://127.0.0.1:5173/kol.html',archive='ARSIV/ESKI_SURUMLER.zip',manufacturing_approved=False,physical_approval=False,print_layout_available=True,design_review=json.loads((CAD/'TUTUCU/STATUS.json').read_text()),rod_joint=json.loads((CAD/'CUBUK_MAFSALI/STATUS.json').read_text()))
    for dest in [CURRENT/'SURUM.json',CAD/'RELEASE_STATUS.json']:dest.write_text(json.dumps(status,indent=2))
    models=ROOT/'viewer/public/models/guncel'
    for f in models.glob('*TRIPOD*'):f.unlink() # generated viewer copies, verified originals archived
    for f in CAD.glob('*.glb'):shutil.copy2(f,models/f.name)
    update_manifest()

def update_manifest():
    from scripts.publish_current import digest
    rows=[dict(path=p.relative_to(CURRENT).as_posix(),bytes=p.stat().st_size,sha256=digest(p)) for p in sorted(CURRENT.rglob('*')) if p.is_file() and p.name!='DOSYA_LISTESI.json']
    (CURRENT/'DOSYA_LISTESI.json').write_text(json.dumps(rows,indent=2))

