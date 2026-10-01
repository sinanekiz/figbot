"""Two-cap replacement kits; validate release inputs and include no G-code."""
import hashlib,json,zipfile
from cad.prototype_arm import build_motor_bearing_pb02 as pb
from cad.prototype_arm import build_forma_v6 as v6


def package(dest,files,readme):
    hashes={name:hashlib.sha256(path.read_bytes()).hexdigest() for path,name in files}
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
        for path,name in files:z.write(path,name)
        z.writestr('ONCE_OKU.md',readme)
        z.writestr('SHA256.json',json.dumps(hashes,indent=2))
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None and not any(n.lower().endswith('.gcode') for n in z.namelist())
        for n,h in hashes.items():assert hashlib.sha256(z.read(n)).hexdigest()==h
    return {'path':str(dest),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'files':len(files)+2}


def main():
    for folder in [pb.OUT,v6.OUT]:
        tests=(folder/'TEST_RESULTS.txt').read_text(encoding='utf-8')
        assert 'passed' in tests and 'failed' not in tests
        qa=json.loads((folder/'OFFLINE_SLICE_AUDIT.json').read_text())
        assert all(r['returncode']==0 and not r['warnings'] for r in qa['results'])
    manifest=json.loads((pb.OUT/'MANIFEST.json').read_text())
    assert manifest['source_sha256']==hashlib.sha256(pb.ROOT.joinpath('cad/prototype_arm/build_motor_bearing_pb02.py').read_bytes()).hexdigest()
    common=[(pb.ROOT/'reports/20260912_RULMAN_KAPAK_BOSLUGU.png','BOSLUK_KESITI.png'),
            (pb.ROOT/'reports/20260912_RULMAN_KAPAK_BOSLUGU.json','BOSLUK_OLCULERI.json')]
    files=common+[(pb.OUT/'TEKIL'/(pid+'.'+ext),pid+'.'+ext)
        for pid in ['PB02_03A_YAN_KAPAK','PB02_03B_YAN_KAPAK'] for ext in ['stl','step']]
    files += [(pb.OUT/'TEST_RESULTS.txt','KONTROL/TEST_RESULTS.txt'),(pb.OUT/'OFFLINE_SLICE_AUDIT.json','KONTROL/OFFLINE_SLICE_AUDIT.json')]
    dest=pb.ROOT/'releases';dest.mkdir(exist_ok=True)
    kits=[package(dest/'FIGBOT_PB02_KAPAK_BOSLUK_R2.zip',files,(pb.OUT/'ONCE_OKU.md').read_text(encoding='utf-8'))]
    files=common+[(v6.OUT/folder/(pid+'.'+ext),folder+'/'+pid+'.'+ext)
        for pid in ['F6-03A-RETAINER','F6-03B-RETAINER']
        for folder,ext in [('PRINT_STL','stl'),('PART_STEP','step'),('3MF','3mf')]]
    kits.append(package(dest/'FIGBOT_FORMA_V6_KAPAK_BOSLUK_R2.zip',files,
        '# FORMA V6 tutucu yarımları — DEC-071\n\nYalnız FORMA V6 içindir; eski PB02 tabana uymaz. F6-03A ve F6-03B birer adet. Köşelerde1,0mm, düz tabla üzerinde1,4mm boşluk; iç dudak2,6mm. STL baskı yönünde, STEP montaj koordinatlarında. 3MF genel dilimleyici ayarı içerir, yazıcı profili değildir. Aynı dış vida bağlantıları kullanılır. Motorlar enerjisiz, kol destekli olarak yüksüz uyum kontrolü gerekli. Fiziksel sürtünme ve dayanım henüz doğrulanmadı.\n'))
    (pb.ROOT/'reports/20260912_RULMAN_KAPAK_PAKETLERI.json').write_text(json.dumps(kits,indent=2),encoding='utf-8')
    print(json.dumps(kits,indent=2))


if __name__=='__main__':main()
