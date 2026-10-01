"""Create an offline prototype archive with validated geometry, not machine jobs."""
import csv,hashlib,json,zipfile
from pathlib import Path
from cad.prototype_arm import build_aero_v5 as a
from cad.prototype_arm.validate_aero_v5 import source_hashes


def main():
    out=a.OUT;geo=json.loads((out/'GEOMETRY_AUDIT.json').read_text())
    qa=json.loads((out/'OFFLINE_SLICE_AUDIT.json').read_text())
    manifest=json.loads((out/'PRINT_MANIFEST.json').read_text())
    assert geo['passed'] and all(r['returncode']==0 and not r['warnings'] and r['modifiers_preserved'] for r in qa['results'])
    assert '25 passed' in (out/'TEST_RESULTS.txt').read_text()
    assert json.loads((out/'STEP_ROUNDTRIP.json').read_text())['passed']
    assert all(r['CAD_vs_view_max_bound_error_mm']<.6 for r in json.loads((out/'ASSEMBLY_PLACEMENT_AUDIT.json').read_text()))
    qty={r['part']:r['qty_per_arm'] for r in manifest}
    costs=json.loads((out/'COST_ESTIMATE.json').read_text())
    costs['actual_slicer_support_and_purge_mass_g']=None
    costs['generic_slicer_filament_g_including_support_and_brim']=sum(r['filament_g_generic_including_support']*qty[r['part']] for r in qa['results'])
    costs['generic_mass_note']='Includes the 3 soft pads evaluated with generic PLA density; not an actual TPU mass or final machine estimate. No purge model; no weighed print.'
    (out/'COST_ESTIMATE.json').write_text(json.dumps(costs,indent=2),encoding='utf-8')
    summary={'part_types':len(manifest),'instances_per_arm':sum(qty.values()),
        'unit_tests_passed':25,'slice_cases':len(qa['results']),
        'regional_modifiers_preserved':True,'geometry_passed':geo['passed'],
        'path_samples':len(geo['path']),'gripper_samples':len(geo['gripper']),'steering_samples':len(geo['steering']),
        'path_max_static_100g_kgfcm':{j:max(r['gravity']['static_kgfcm'][j] for r in geo['path']) for j in ['shoulder','elbow','wrist']},
        'full_horizontal_static_screen':geo['horizontal_screen'],
        'generic_filament_g_including_support':costs['generic_slicer_filament_g_including_support_and_brim'],
        'physical_strength_validated':False,'motor_fit_validated':False,'fruit_grasp_validated':False,
        'printer_job_sent':False,'live_motor_commands_sent':False,'purchases_made':False}
    (out/'VALIDATION_SUMMARY.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    (out/'EXPORT_SOURCES.json').write_text(json.dumps(source_hashes(),indent=2),encoding='utf-8')
    with (out/'DIMENSIONS.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f,delimiter=';');w.writerow(['dimension','nominal_mm','status'])
        for n,v in [('upper_span',180),('fore_span',140),('base_to_shoulder',124),('rover_shoulder_height',190),
            ('tool_forward_offset',34),('tool_downward_offset',110),('cam_outer_diameter',76),('guide_outer_diameter',88),
            ('compression_sleeve_length',30),('compression_sleeve_OD',6),('compression_sleeve_ID',4),('sleeve_bore',6.25),
            ('finger_radial_stroke',14),('cam_follower_length',9.2),('passive_pivot_bore',6.4)]:
            w.writerow([n,v,'PROTOTYPE / PHYSICAL VALIDATION REQUIRED'])
    paths=[]
    for folder in ['PRINT_STL','PART_STEP','SLICER_3MF','URDF','VIEWS']:
        paths.extend(p for p in (out/folder).rglob('*') if p.is_file())
    names=['ONCE_OKU.md','BASKI_AYARLARI.md','MONTAJ_KILAVUZU.md','MUHENDISLIK_NOTU.md','NOTICE.md','BUILD_COMMANDS.md',
        'PRINT_MANIFEST.json','PRINT_QUANTITIES.csv','HARDWARE_BOM.csv','COST_ESTIMATE.json','GEOMETRY_AUDIT.json',
        'OFFLINE_SLICE_AUDIT.json','STEP_ROUNDTRIP.json','ASSEMBLY_PLACEMENT_AUDIT.json','VALIDATION_SUMMARY.json','EXPORT_SOURCES.json','TEST_RESULTS.txt','DIMENSIONS.csv']
    paths.extend(out/n for n in names)
    for stem in ['AERO_V5_ASSEMBLY','ROVER_PICKUP_REVIEW','ROVER_RELEASE_REVIEW']:
        paths.extend(out/(stem+ext) for ext in ['.step','.glb'])
    hashes={p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    (out/'SHA256.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8');paths.append(out/'SHA256.json')
    dest=a.ROOT/'releases/FIGBOT_AERO_V5_BASKI_PROTOTIPI.zip';dest.parent.mkdir(exist_ok=True)
    sources=['cad/prototype_arm/build_aero_v5.py','cad/prototype_arm/export_aero_v5.py','cad/prototype_arm/validate_aero_v5.py',
        'cad/prototype_arm/qa_aero_v5.py','cad/prototype_arm/qa_step_aero_v5.py','scripts/build_aero_v5_hardware.py','scripts/package_aero_v5.py','tests/test_aero_v5.py']
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(paths):z.write(p,'AERO_V5/'+p.relative_to(out).as_posix())
        for f in sources:z.write(a.ROOT/f,'AERO_V5/SOURCE_SNAPSHOT/'+f)
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None and not any(n.lower().endswith('.gcode') for n in z.namelist())
        for f,h in hashes.items():assert hashlib.sha256(z.read('AERO_V5/'+f)).hexdigest()==h
    fit=dest.with_name('FIGBOT_AERO_V5_ILK_UYUM_TESTI.zip')
    with zipfile.ZipFile(fit,'w',zipfile.ZIP_DEFLATED) as z:
        for pid in ['S03B-BODY','S03B-CAP']:
            for folder,ext in [('PRINT_STL','stl'),('PART_STEP','step'),('SLICER_3MF','3mf')]:
                z.write(out/folder/(pid+'.'+ext),folder+'/'+pid+'.'+ext)
        z.write(out/'NOTICE.md','NOTICE.md')
        z.writestr('ONCE_OKU.txt',
            'AERO V5 — ilk MG90S başlık uyum testi\n\n'
            'S03B-BODY: 1 adet. S03B-CAP: 2 adet.\n'
            'Bu küçük set son gönderdiğin Arm03 başlık konturuna göre hazırlanmıştır. Gerçek başlık uyumu henüz doğrulanmadı.\n'
            'Orijinal MG90S plastik başlığını ve motorun kendi merkez vidasını kullan. Mil spline dişlisi basılmaz.\n'
            'Enerjisiz kontrol: başlık cebine tam oturuş, kapakların kapanması, boşluk ve merkez vida erişimi. Zorlayarak geçirme.\n'
            '0,4mm meme / 0,2mm katman ilk deneme bağlamı; gerçek yazıcı ve filament profilini seç.\n'
            'STL dolgu ayarı içermez.3MF içindeki ayar PrusaSlicer2.8.1 ile kontrol edildi; G-code yoktur.\n'
            'Bu test motor hareketi, yük kapasitesi veya diğer kol parçalarının fiziksel onayı değildir.\n'
            'Tam kol, montaj ve metal donanım listesi FIGBOT_AERO_V5_BASKI_PROTOTIPI.zip içindedir.\n')
    with zipfile.ZipFile(fit) as z:assert z.testzip() is None
    print(json.dumps({'archive':str(dest),'first_fit_archive':str(fit),'bytes':dest.stat().st_size,'files':len(paths)+len(sources),'summary':summary},indent=2),flush=True)


if __name__=='__main__':main()
