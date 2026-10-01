"""Release checked CAD prototypes + separate small fit package. No G-code."""
import hashlib,json,zipfile,csv
from cad.prototype_arm import build_forma_v6 as a
from cad.prototype_arm.validate_forma_v6 import source_hashes

def main():
    out=a.OUT
    release_status=out/'RELEASE_STATUS.json'
    if release_status.exists():
        status=json.loads(release_status.read_text(encoding='utf8'))
        if not status.get('allow_full_arm_package',False):
            raise RuntimeError(f"Full-arm packaging on hold: {status.get('decision')} — {status.get('reason')}")
    geo=json.loads((out/'VALIDATION.json').read_text());qa=json.loads((out/'OFFLINE_SLICE_AUDIT.json').read_text())
    manifest=json.loads((out/'MANIFEST.json').read_text());tests=(out/'TEST_RESULTS.txt').read_text()
    assert geo['sources']==source_hashes() and 'passed' in tests and 'failed' not in tests
    assert not geo['neutral_hits'] and all(r['valid'] and r['solids']==1 for r in geo['parts'])
    path=list(geo['targets'].values())+geo['path']
    assert all(not r['hits'] and not r['vehicle']['hits'] for r in path)
    assert all(not r['hits'] for r in geo['gripper_sweep']+geo['steering'])
    assert all(r['returncode']==0 and r['roundtrip_returncode']==0 and r['modifiers_preserved'] and not r['warnings'] for r in qa['results'])
    for r in qa['results']:
        assert hashlib.sha256((out/'3MF'/(r['part']+'.3mf')).read_bytes()).hexdigest()==r['input_sha256']
        assert all(all(int(v)==0 for v in repair.values()) for repair in r['mesh_repairs'])
    summary={'status':'CAD AND FIRST-FIT PROTOTYPE / PHYSICAL VALIDATION REQUIRED',
       'revision':a.REVISION,'unique_exported_parts':len(manifest),'small_fit_part_types':6,'closure_part_types':2,'bench_unique_part_types':14,'optional_rover_receiver':True,
       'modeled_mass_g':geo['horizontal_screen']['modeled_mass_g'],
       'sampled_path_max_static_kgf_cm':{j:max(r['gravity']['static_kgf_cm'][j] for r in path) for j in ['shoulder','elbow','wrist']},
       'payload_g':100,'extra_scenario_allowance_g':25,'target_and_path_samples':len(path),'gripper_samples':6,'steering_samples':13,
       'retainer_clearance_revision':'R6 retains DEC-074 running clearances: footprint120x120, roof5.1, 1.0mm cornergap /1.4mm flangegap; physical fit unverified',
       'physical_fit_validated':False,'physical_strength_validated':False,'fruit_grip_validated':False,
       'printer_jobs_sent':False,'motor_commands_sent':False,'purchases_made':False}
    (out/'VALIDATION_SUMMARY.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
    interfaces={'status':'J1 body/shaft USER-REPORTED; all other interfaces UNVERIFIED - fit check before full-arm print',
      'revision':a.REVISION,'MG996R':a.MG,'MG90S':a.MICRO,
      'external_socket_screw_axes_mm':{'MG996R':a.horn_points(False),'MG90S':a.horn_points(True)},
      'horn_references':a.original_horns.provenance(),
      'J1_measured_specimen':{'raw_measurements':a.YAW_MEASUREMENTS,'CAD_parameters':a.YAW_MG,
          'mount_opening':a.YAW_MOUNT,'mount_revision':'DEC-073: preserve old aperture; cable and assembly path UNVERIFIED',
          'near_case_face_to_axis_mm':10.15,'body_center_to_axis_mm':9.8,'decision':'DEC-072',
          'unverified':['width','height','ear pattern and location','ear elevation','shaft transverse offset','horn fit','physical concentricity']},
      'base_mount_M4_pitch_mm':[100,100],'M4_receiver_pilot_mm':[5.6,6],
      'retainer_roof':{'minimum_corner_gap_mm':a.RETAINER_AXIAL_CLEARANCE,'plain_flange_gap_mm':1.4,'inner_roof_thickness_mm':5.1,'relief_outer_radius_mm':58,'footprint_mm':[120,120],'decision':'DEC-074'},
      'finger_pivot':{'bore_mm':3.2,'smooth_sleeve_OD_mm':3,'smooth_sleeve_ID_mm':2.1,'sleeve_length_mm':4.6,'ear_gap_mm':4.8},
      'passive_pivot':{'bore_mm':6.2,'smooth_sleeve_OD_mm':6,'smooth_sleeve_ID_mm':3.3,'lengths_mm':[11.5,15.5]},
      'dimensions_source':'J1 length/shaft OD/longitudinal offset from user readings39.9/7.3/5.7mm; others remain explicit trial parameters. See DEC-072 and ONCE_OKU.md.'}
    (out/'INTERFACES.json').write_text(json.dumps(interfaces,indent=2),encoding='utf8')
    (out/'HORN_REFERENCES.json').write_text(json.dumps(a.original_horns.provenance(),indent=2),encoding='utf8')
    with (out/'PARCA_LISTESI.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f,delimiter=';');w.writerow(['parca','adet','sinif','malzeme','CAD_tam_malzeme_g'])
        for r in manifest:w.writerow([r['part'],r['qty'],r['type'],r['material'],round(r['CAD_full_material_g'],2)])
    paths=[p for folder in ['PRINT_STL','PART_STEP','3MF','URDF','VIEWS'] for p in (out/folder).rglob('*') if p.is_file()]
    paths += [p for p in out.iterdir() if p.is_file() and p.suffix in ['.step','.glb','.md','.csv','.json','.txt'] and p.name!='SHA256.json']
    paths=sorted(set(paths));hashes={p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    (out/'SHA256.json').write_text(json.dumps(hashes,indent=2),encoding='utf8');paths.append(out/'SHA256.json')
    dest=a.ROOT/'releases/FIGBOT_FORMA_V6_CAD_PROTOTIP.zip';dest.parent.mkdir(exist_ok=True)
    sources=['cad/prototype_arm/'+n for n in ['build_forma_v6.py','forma_v6_horns.py','export_forma_v6.py','validate_forma_v6.py','integrate_forma_v6.py','qa_forma_v6.py']]
    sources += ['scripts/build_forma_v6_hardware.py','scripts/package_forma_v6.py','tests/test_forma_v6.py','tests/test_forma_v6_r5.py','tests/test_forma_v6_r6.py','MASTER_SPEC.md','DECISIONS.md','ASSUMPTIONS.md','viewer/forma-v6.html']
    sources += [p.relative_to(a.ROOT).as_posix() for p in a.original_horns.SOURCES.values()]
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
        for p in paths:z.write(p,'FORMA_V6/'+p.relative_to(out).as_posix())
        for p in sources:z.write(a.ROOT/p,'FORMA_V6/SOURCE_SNAPSHOT/'+p)
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None and not any(p.lower().endswith('.gcode') for p in z.namelist())
        for p,h in hashes.items():assert hashlib.sha256(z.read('FORMA_V6/'+p)).hexdigest()==h
    fit=dest.with_name('FIGBOT_FORMA_V6_ILK_UYUM.zip')
    with zipfile.ZipFile(fit,'w',zipfile.ZIP_DEFLATED) as z:
        for pid in ['F6-12-EAR-FIT','F6-14-MICRO-FIT','F6-15-INSERT-FIT','F6-17-YAW-FIT','F6-18-LARGE-HORN-FIT','F6-19-MICRO-HORN-FIT','F6-20-LARGE-SOCKET-COVER','F6-21-MICRO-SOCKET-COVER']:
            for folder,ext in [('PRINT_STL','stl'),('PART_STEP','step'),('3MF','3mf')]:z.write(out/folder/(pid+'.'+ext),folder+'/'+pid+'.'+ext)
        for name in ['ONCE_OKU.md','INTERFACES.json','HORN_REFERENCES.json']:z.write(out/name,name)
        for name in ['01_YENI_KOL.png','04_PICKUP.png','05_RELEASE.png','07_ORIGINAL_BASLIKLAR.png','08_YILDIZ_YUVASI_ACIK.png']:z.write(out/'VIEWS'/name,'VIEWS/'+name)
        z.writestr('BASLANGIC.txt','R6: Önce ONCE_OKU.md. Altı uyum numunesi ve F6-20/F6-21 kapama parçaları. F6-18 büyük yıldız yuvası F6-20 ile; F6-19 küçük yıldız yuvası F6-21 ile denenir. Başlıklar orijinaldir, basılmaz. Küçük deliklere vida girmez; dış kapak iki M2x6 ile insertlere bağlanır. Orijinal merkez vida kendi metal miline girer. Tam kol fiziksel uyum/yük onaylı değil; G-code yok.')
    with zipfile.ZipFile(fit) as z:assert z.testzip() is None
    basekit=dest.with_name('FIGBOT_FORMA_V6_TABAN_R6.zip')
    basefiles=[]
    for pid in ['F6-01-BASE','F6-02-ROTOR','F6-03A-RETAINER','F6-03B-RETAINER','F6-17-YAW-FIT','F6-18-LARGE-HORN-FIT','F6-20-LARGE-SOCKET-COVER']:
        for folder,ext in [('PRINT_STL','stl'),('PART_STEP','step'),('3MF','3mf')]:
            basefiles.append(out/folder/(pid+'.'+ext))
    basefiles += [out/n for n in ['ONCE_OKU.md','INTERFACES.json','VALIDATION_SUMMARY.json','TEST_RESULTS.txt']]
    basefiles.append(out/'VIEWS/02_BILYELI_TABAN.png')
    basehash={p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in basefiles}
    with zipfile.ZipFile(basekit,'w',zipfile.ZIP_DEFLATED) as z:
        for p in basefiles:z.write(p,p.relative_to(out).as_posix())
        z.writestr('SHA256.json',json.dumps(basehash,indent=2))
        z.writestr('TABAN_PAKETI.txt',
            'FORMA V6 R6 / DEC-075. Ölçülen J1: gövde39,9mm; mil5,7mm; gövde merkezi-mil ofseti9,80mm. '
            'Eski yuva açıklığı41,5x20,5mm korunur; gövde ölçümü yüzünden daraltılmaz. '
            'Kablo çıkıntısı, fiş ve montaj yolu henüz doğrulanmadı. Bu paket montaj tamamlandı onayı değildir. '
            'Önce küçük F6-17-YAW-FIT numunesi ile gövde ve vida kulaklarını dene. '
            'F6-01 taban, F6-02 rotor ve F6-03A/B üst kapaklar eşleşen R6 takımıdır. Her birinden1 adet. F6-20 yıldız kapamasını da ekle. '
            'Kapaklar120x120mm sınırda, iç dudak5,1mm; dönüş boşluğu1/1,4mm korunur. M3x20 vidalarda eski2,5mm ara pulları kullanılmaz. '
            'F6-18 orijinal büyük başlığın şekilli yuvasını F6-20 ile sınar. Yıldızın çevre delikleri kullanılmaz; iki dış M2x6 vida kapamayı insertlere tutturur. '
            'Bu paket yalnız güncellenen taban parçaları ve numunedir; tam kol dosyaları ana pakettedir. '
            'Eski PB02 ile parça uyumu yoktur. Ölçülmeyen kulak düzeni/en/yükseklik ve diğer motorlar aday ölçüdedir. '
            'Gerçek montaj merkezlemesi ve yük dayanımı doğrulanmadı. Motor enerjisiz, mekanizma destekli kontrol edilir. '
            'Yazıcıya veya motora komut gönderilmedi; G-code yoktur.')
    with zipfile.ZipFile(basekit) as z:
        assert z.testzip() is None and not any(n.lower().endswith('.gcode') for n in z.namelist())
        for n,h in basehash.items():assert hashlib.sha256(z.read(n)).hexdigest()==h
    print(json.dumps({'CAD':str(dest),'first_fit':str(fit),'measured_base':str(basekit),'summary':summary},indent=2),flush=True)

if __name__=='__main__':main()
