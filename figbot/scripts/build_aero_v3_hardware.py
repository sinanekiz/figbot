"""Dedicated V3 mechanical BOM; do not edit purchased-inventory/cost ledgers."""
import csv
from decimal import Decimal
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ROWS=[
('MG996R',4,'servo','225.405','User order: 4 for 901.62 TRY incl VAT','Existing purchased stock; four per arm'),
('MG90S',2,'servo','116.935','User orders: 116.19 + 117.68 TRY incl VAT','Existing two purchased units; G1 + W1'),
('Aluminium tube 20x20x1.5 - 235 mm',1,'piece','','TBD','Upper tube; verify coupon and cut/drill to drawing'),
('Aluminium tube 20x20x1.5 - 161 mm',1,'piece','','TBD','Fore tube; verify coupon and cut/drill to drawing'),
('M3x16 machine screw',24,'piece','','TBD','Four servo-clamp bolts per actuator'),
('M3x30 machine screw',2,'piece','','TBD','Removable wrist drive plate to palm'),
('M3 locking nut',26,'piece','','TBD','Servo clamps + wrist plate'),
('M3 washer',52,'piece','','TBD','Two per M3 bolt'),
('M4x35 machine screw',8,'piece','','TBD','Four drilled holes per aluminium tube'),
('M4x20 machine screw',8,'piece','','TBD','Four yaw-deck joints + four base mounts to 6 mm plate; bench board thickness changes mount length'),
('M4x12 axle screw',2,'piece','','TBD','Captive nut + printed journal sleeve; J3 and W1'),
('M4 locking nut',16,'piece','','TBD','Tube and base joints'),
('M4 regular hex nut',2,'piece','','TBD','Side-loaded idler traps: nominal 7 mm AF, 3.2 mm thick; verify actual nut'),
('M4 washer',32,'piece','','TBD','Tube and base joints; idler thrust washers are PRINTED'),
('M2x10 coupling screw',14,'piece','','TBD','Up to 4 each J2L/J2R/J3; 2 W1. Validate supplied horn hole pitch'),
('M2x12 coupling screw',4,'piece','','TBD','J1 recessed head pockets; validate horn stack before tightening'),
('M2x20 coupling screw',2,'piece','','TBD','G1 moving jaw; validate horn stack'),
('M2 nut',20,'piece','','TBD','Horn couplings; actual supplied horn may accept only two opposite holes'),
('M2 washer',40,'piece','','TBD','Horn couplings'),
('Supplied servo horn + original centre screw',6,'set','','Included with actuator; confirm contents','Never print the spline; use the matching horn from each servo'),
('Soft pad 3 mm - fixed 12x12 / moving 12x12',2,'piece','','TBD','Foam/silicone candidate; food contact and adhesion unverified'),
('PETG filament',1,'job','','TBD','Mass from slicer; supports and failed prints not included'),
]

def build():
    assert len({r[0] for r in ROWS})==len(ROWS)
    assert all(r[1]>0 for r in ROWS)
    known=sum(Decimal(str(r[1]))*Decimal(r[3]) for r in ROWS if r[3])
    assert known==Decimal('1135.49')
    dest=ROOT/'bom/AERO_V3_BENCH_HARDWARE.csv'
    with dest.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f);w.writerow(['item','qty','unit','unit_try_incl_vat','price_source','note']);w.writerows(ROWS)
    text=(f'# AERO V3 bench BOM cost\n\nKnown actuator allocation only: {known} TRY incl VAT; {known/Decimal("1.2"):.2f} TRY excl assumed 20% VAT. '
          'This uses supplied historical order totals, not a current supplier quotation or a new purchase.\n\n'
          'TOTAL BUILD COST: UNKNOWN. Tubes, fasteners, pads, filament, freight, labour and failed prints are unpriced (TBD), NOT zero. '
          'The existing purchasing spreadsheet is unchanged; do not add this allocation to its totals again.\n\n'
          'Two MG90S are used on one arm: gripper and active wrist. The two-arm vehicle view does not mean a second hardware set was purchased.\n')
    (ROOT/'reports/AERO_V3_BENCH_COST.md').write_text(text,encoding='utf-8')
    print('Validated V3 hardware: known actuator allocation',known,'TRY; total UNKNOWN')
    return known

if __name__=='__main__':build()
