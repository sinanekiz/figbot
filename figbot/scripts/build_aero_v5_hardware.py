"""Candidate bench hardware and unknown-inclusive cost, no inventory mutation."""
import csv,json
from decimal import Decimal
from cad.prototype_arm import build_aero_v5 as a

ROWS=[
 ('MG996R',4,'servo','225.405','Existing historical order allocation','J1, paired J2, J3; not a new purchase'),
 ('MG90S',2,'servo','116.935','Existing historical order allocation','W1 and G1; clone fit UNVERIFIED'),
 ('M3x40 socket-head screw',9,'piece','','TBD','Split shells: 5 upper, 4 fore'),
 ('Aluminium tube OD6 ID4 length30 mm',9,'piece','','TBD','Compression sleeve; square ends, deburr; verify flush against 30mm lands'),
 ('M3x20 socket-head screw',28,'piece','','TBD','24 motor clamps and 4 removable shoulder towers; stack/clearance fit test'),
 ('M3x16 socket-head screw',10,'piece','','TBD','8 large horn-tongue receivers and 2 wrist receivers'),
 ('M3 nylon locking nut',47,'piece','','TBD','9+28+10; do not substitute printed pins'),
 ('M3 washer OD7 thickness0.5 mm',94,'piece','','TBD','Two per M3 screw; actual thickness affects stack'),
 ('Shoulder screw shaft6 length16 threadM5',2,'piece','','TBD','Elbow and wrist passive pivots; smooth shaft at bearing surfaces'),
 ('M5 nylon locking nut',2,'piece','','TBD','For passive shoulder screws; retain endfloat, do not jam rotating parts'),
 ('M5 thin washer thickness0.5 mm',4,'piece','','TBD','Two per passive pivot; adjust shim after fit'),
 ('M2x16 screw',3,'piece','','TBD','Cam followers; NOT a clamp through the moving cam'),
 ('Brass tube OD3 ID2.1 length9.2 mm',3,'piece','','TBD','Cam follower sleeves, nominal0.4mm axial running allowance'),
 ('M2 washer OD5 thickness0.5 mm',10,'piece','','TBD','6 followers, 4 cam retainer'),
 ('M2x10 screw',2,'piece','','TBD','Recessed original-horn retainer cap'),
 ('M2 nylon locking nut',5,'piece','','TBD','Followers3 + retainer2'),
 ('Original supplied horn and centre screw',6,'set','','Included with motors; verify','Never print spline, use original correct centre screw'),
 ('M4 mounting bolt nut washer set',4,'set','','TBD','Base100x86 pattern; length depends on actual carrier/bench thickness'),
 ('Soft TPU pads OR fitted silicone pads',3,'piece','','TBD','19x12x4 nominal; food contact, friction and compliance UNVERIFIED'),
 ('Soft pad tie cord',1,'length','','TBD','Six tie passages; cleanable attachment and material selection pending'),
 ('PLA filament',1,'job','','TBD','First-fit prototype; actual brand/profile/price unknown'),
]


def main():
    manifest=json.loads((a.OUT/'PRINT_MANIFEST.json').read_text())
    dest=a.OUT/'HARDWARE_BOM.csv'
    with dest.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f,delimiter=';');w.writerow(['item','qty_per_arm','unit','unit_TRY','source','note']);w.writerows(ROWS)
    known=sum(Decimal(r[3])*r[1] for r in ROWS if r[3])
    assert known==Decimal('1135.49')
    estimate={'status':'CANDIDATE BOM; TOTAL COST UNKNOWN','historical_existing_motor_allocation_TRY':str(known.quantize(Decimal('.01'))),
       'new_motor_purchase_required':False,'total_build_cost_TRY':None,'new_hardware_cost_TRY':None,
       'filament_TRY_kg':None,'print_cost_TRY':None,'unpriced_lines':sum(not r[3] for r in ROWS),
       'cad_PLA_density_g_mm3':.00124,
       'new_rigid_parts_full_material_g':sum(p['qty_per_arm']*p['volume_mm3']*.00124 for p in manifest if p['class'] not in ['TPU','reuse_or_fit','fit_first']),
       'horn_adapters_full_material_g':sum(p['qty_per_arm']*p['volume_mm3']*.00124 for p in manifest if p['class'] in ['reuse_or_fit','fit_first']),
       'actual_slicer_support_and_purge_mass_g':None,'purchase_ledger_changed':False,
       'scope':'Per one arm; two rover positions do not establish a second owned motor set. Full-material CAD volume estimate excludes supports, waste and uncertain density. Unknown prices are not zero.'}
    (a.OUT/'COST_ESTIMATE.json').write_text(json.dumps(estimate,indent=2),encoding='utf-8')
    assert len({r[0] for r in ROWS})==len(ROWS) and all(r[1]>0 for r in ROWS)
    assert 9+28+10==47 and 47*2==94
    print(json.dumps(estimate,indent=2),flush=True)
    return estimate


if __name__=='__main__':main()
