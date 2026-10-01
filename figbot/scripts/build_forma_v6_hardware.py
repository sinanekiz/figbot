"""One-arm candidate hardware; unknown prices remain unknown. No purchases."""
import csv,json
from decimal import Decimal
from cad.prototype_arm import build_forma_v6 as a

ROWS=[
 ('MG996R',4,'piece','225.405','Historical order allocation; see V5 hardware record','Existing: yaw1, shoulder2, elbow1'),
 ('MG90S',2,'piece','116.935','Historical order allocation; see V5 hardware record','Existing: wrist1, gripper1'),
 ('Original horn and original shaft screw',6,'set','','Included with servo; verify','Original centre screw into metal shaft; do not substitute'),
 ('M3 heat-set insert L5 OD TBD',22,'piece','','TBD','16 servo ears +4 bearing retainer +2 passive joints; pilot4.2 candidate'),
 ('M2 heat-set insert L4 OD TBD',22,'piece','','TBD','4 micro ears +12 socket closure holes +3 finger pivots +3 soft pads; pilot2.9 candidate'),
 ('M4 heat-set insert L6 OD TBD',4,'piece','','TBD','OPTIONAL rover receiver plate; pilot5.6 candidate'),
 ('M3x8 screw',16,'piece','','TBD','Factory MG996R ears; 1mm washer assumed; actual ear thickness UNVERIFIED'),
 ('M3 washer thickness1',16,'piece','','TBD','Large servo ears'),
 ('M2x6 screw',16,'piece','','TBD','4 micro ears with0.5mm washer +12 external socket-closure screws; no factory horn hole used'),
 ('M2 washer thickness0.5',10,'piece','','TBD','4 micro ears +3 pivot +3 pad; confirm clearance'),
 ('M3x20 screw retainer',4,'piece','','TBD','R5 retainer15.5mm; no old2.5mm shim; nominal4.5mm insert engagement'),
 ('M3x16 screw passive elbow',1,'piece','','TBD','11.5mm sleeve +1mm washer +3.5mm engagement'),
 ('M3x20 screw passive wrist',1,'piece','','TBD','15.5mm sleeve +1mm washer +3.5mm engagement'),
 ('M3 washer thickness1 passive',2,'piece','','TBD','Passive sleeves, not squeezing moving boss'),
 ('Smooth sleeve OD6 ID3.3 L11.5',1,'piece','','TBD','Metal tube, square ends; elbow; ~0.1mm radial nominal clearance'),
 ('Smooth sleeve OD6 ID3.3 L15.5',1,'piece','','TBD','Metal tube, wrist; must not use threaded shank as bearing'),
 ('M2x14 screw finger pivot',3,'piece','','TBD','Candidate axial stack; confirm insert bottom clearance and free rotation'),
 ('Smooth sleeve OD3 ID2.1 L4.6',3,'piece','','TBD','4mm finger between4.8mm ears; physical running clearance test'),
 ('M2x9 screw pad',3,'piece','','TBD','6mm pad +0.5 washer +2.5 engagement; custom length or verify available substitute'),
 ('M4x10 screw receiver',4,'piece','','TBD','OPTIONAL: base4mm +1washer +5 engagement'),
 ('M4 washer thickness1',4,'piece','','TBD','OPTIONAL receiver'),
 ('Diameter8 ball',24,'piece','','PB02 stock or printed candidate, verify','No new steel-ball mass assumption; exported sphere is optional'),
 ('Tendon cord diameter TBD',3,'length TBD','','TBD','Three cord legs; low stretch; routing and friction test required'),
 ('Elastic return element',3,'piece','','TBD','One per finger; preload and closing force are UNVERIFIED'),
 ('Soft pad TPU or cut silicone',3,'piece','','TBD','Actual hardness/food contact/grasp pressure unverified'),
 ('PLA filament',1,'print job','','TBD','Sliced material, supports, rate and measured density unknown'),
 ('Rover receiver to frame connection',1,'assembly TBD','','TBD','Not released: contextual truss is not a fabricated chassis joint'),
]

def main():
    manifest=json.loads((a.OUT/'MANIFEST.json').read_text(encoding='utf8'))
    with (a.OUT/'HARDWARE_BOM.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f,delimiter=';');w.writerow(['item','qty_one_arm','unit','unit_TRY','source','note']);w.writerows(ROWS)
    known=sum(Decimal(r[3])*r[1] for r in ROWS if r[3])
    assert known==Decimal('1135.490')
    cost={'status':'CANDIDATE / TOTAL UNKNOWN','historical_existing_motors_TRY':str(known.quantize(Decimal('.01'))),
       'new_hardware_cost_TRY':None,'total_build_cost_TRY':None,'print_cost_TRY':None,'filament_TRY_kg':None,
       'new_motor_purchase_required':False,'purchase_ledger_changed':False,'unpriced_lines':sum(not r[3] for r in ROWS),
       'full_material_rigid_bench_parts_g':sum(r['qty']*r['CAD_full_material_g'] for r in manifest if r['type'] not in ['fit','integration'] and 'PAD' not in r['part']),
       'actual_sliced_mass_g':None,'scope':'One arm. Optional rover receiver counted separately. Unknown is not zero. Existing motor allocation is not a new order cost.'}
    (a.OUT/'COST_ESTIMATE.json').write_text(json.dumps(cost,indent=2),encoding='utf8')
    assert len({r[0] for r in ROWS})==len(ROWS) and all(r[1]>0 for r in ROWS)
    assert 16+4+2==22 and 4+12+3+3==22
    print(json.dumps(cost,indent=2),flush=True)
    return cost

if __name__=='__main__':main()
