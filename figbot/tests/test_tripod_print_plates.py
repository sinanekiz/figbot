"""Check delivered quantities, source identity, bed geometry and slicer evidence."""
import json,hashlib,zipfile
from collections import Counter
import numpy as np
import trimesh
from scripts.project_paths import ROOT,CAD,PRINTS
from scripts.package_tripod_plates import REMOVED,entry,check
from scripts.package_twin_plates import NEW

def manifest():return json.loads((PRINTS/'TABLA_LISTESI.json').read_text(encoding='utf-8'))

def test_full_arm_counts_exclude_obsolete_gripper():
    counts=Counter(i['id'] for p in manifest()['plates'] for i in p['instances'])
    assert sum(counts.values())==34
    assert not REMOVED.intersection(counts)
    assert not any(k.startswith('RT-') for k in counts)
    assert {k:v for k,v in counts.items() if k.startswith('TS-')}=={'TS-FRAME':1,'TS-BRIDGE':1,'TS-JAW-DRIVE':1,'TS-JAW-PASSIVE':1,'TS-BUSH':1}
    assert counts['J1-CAPTURE-CUP']==1 and counts['L1-20-MG-COVER']==3
    assert counts['L1-25-FINGER-BUSH']==0 and counts['L1-21-MICRO-COVER']==2
    assert counts['L1-09-UPPER-TIE']==2 and counts['L1-12-FORE-TIE']==1

def test_new_layout_preserves_geometry_and_has_bed_and_brim_space():
    for name,layout in NEW.items():
        entries=[];count=Counter()
        for pid,x,y in layout:
            angles=(0,0,0)
            count[pid]+=1;src=CAD/'TUTUCU/PROTOTIP_STL'/f'{pid}.stl'
            e=entry(pid,count[pid],x,y,angles,src);entries.append(e)
            assert e['mesh'].volume==__import__('pytest').approx(trimesh.load_mesh(src).volume,rel=1e-6)
        check(entries)
        delivered=trimesh.load_mesh(PRINTS/name/(name+'.stl'))
        assert delivered.is_watertight
        assert len(delivered.split())==len(entries)
        assert np.allclose(delivered.bounds,trimesh.util.concatenate([e['mesh'] for e in entries]).bounds,atol=1e-4)

def test_real_3mf_objects_and_archived_obsolete_packages():
    import xml.etree.ElementTree as ET
    q='{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}'
    for name,layout in NEW.items():
        with zipfile.ZipFile(PRINTS/name/(name+'.3mf')) as z:
            model=ET.fromstring(z.read('3D/3dmodel.model'))
            assert model.get('unit')=='millimeter'
            assert len(model.find(q+'build'))==len(layout)
    assert not (PRINTS/'04A_YALNIZ_YENI_PARMAKLAR').exists()
    assert not (PRINTS/'05_YUMUSAK_PEDLER').exists()

def test_delivered_new_plates_were_sliced_without_errors():
    report=json.loads((CAD/'TUTUCU/PRINT_SLICE_AUDIT.json').read_text())
    assert report['printer_commands_sent'] is False and report['physical_approval'] is False
    assert len(report['results'])==4
    for r in report['results']:
        p=PRINTS/r['plate']/(r['plate']+'.3mf')
        assert hashlib.sha256(p.read_bytes()).hexdigest()==r['input_sha256']
        assert r['returncode']==0 and not r['warnings'] and r['layer_count']>5
