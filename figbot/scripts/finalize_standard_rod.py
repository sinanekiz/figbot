"""Refresh current metadata after DEC-085 exports and shopping generation."""
import json,hashlib,shutil
from scripts.project_paths import ROOT,CAD,PRINTS
from scripts.export_rigid_tripod import procurement

def main():
    joint=CAD/'CUBUK_MAFSALI'
    mass=json.loads((joint/'MASS_AND_PARTS.json').read_text())
    shutil.copy2(joint/'MASS_AND_PARTS.json',CAD/'MASS_AND_PARTS.json')
    manifest=json.loads((PRINTS/'TABLA_LISTESI.json').read_text())
    import trimesh
    total=0
    for plate in manifest['plates']:
        for e in plate['instances']:
            source=ROOT/e['source'] if 'source' in e else CAD/'PRINT_STL'/f"{e['id']}.stl"
            total+=trimesh.load_mesh(source).volume*.00124
    cost=dict(revision='DEC-085',status='PRICING INCOMPLETE; no purchase',currency='TRY',printed_part_instances=49,cad_solid_mass_g=total,filament_price_per_kg=None,hardware_total=None,total=None,note='Solid-volume estimate, not weighed. Supports and actual filament price unknown. Historical partial hardware cost: ALISVERIS/VERI/MALIYET.json.')
    (CAD/'COST_ESTIMATE.json').write_text(json.dumps(cost,indent=2))
    rows=json.loads((PRINTS/'PARCA_KARSILASTIRMA.json').read_text())
    for row in rows:
        if row['part']=='L1-15-COUPLER':
            row.update(new_sha256=hashlib.sha256((CAD/'PRINT_STL/L1-15-COUPLER.stl').read_bytes()).hexdigest().upper(),unchanged=False,revision='DEC-085')
    (PRINTS/'PARCA_KARSILASTIRMA.json').write_text(json.dumps(rows,indent=2))
    status=json.loads((joint/'STATUS.json').read_text())
    status['geometry_sha256']={pid:hashlib.sha256((CAD/'PRINT_STL'/f'{pid}.stl').read_bytes()).hexdigest() for pid in status['reprint']+status['reuse']}
    (joint/'STATUS.json').write_text(json.dumps(status,indent=2))
    status=json.loads((CAD/'RELEASE_STATUS.json').read_text())
    status.update(revision='DEC-085',manufacturing_approved=False,physical_approval=False)
    (CAD/'RELEASE_STATUS.json').write_text(json.dumps(status,indent=2))
    (CAD/'TUTUCU/MALZEME_KARSILASTIRMASI.json').write_text(json.dumps(procurement(),ensure_ascii=False,indent=2),encoding='utf-8')
    (CAD/'ASSEMBLY_NOTES_TR.md').write_text('# Güncel montaj notları — DEC-085\n\nÇubuk: CUBUK_MAFSALI/MONTAJ.md. Tutucu: TUTUCU/OKU.md. Yeni çubuk09 tablasında. Eski omuzlu vida/M4 pullar kullanılmaz. Tutucunun bildirilen kırılganlığı henüz giderilmedi. Motorlu yük testi onayı yok.\n',encoding='utf-8')
    for suffix,source in [('GRIPPER','TRIPOD_OPEN'),('GRIPPER_CLOSED','TRIPOD_CLOSED')]:
        for ext in ['glb','step']:
            shutil.copy2(CAD/'TUTUCU'/f'LINKA_L1_{source}.{ext}',CAD/f'LINKA_L1_{suffix}.{ext}')

if __name__=='__main__':main()
