from decimal import Decimal
from scripts.build_aero_v3_hardware import ROWS

def test_existing_actuator_allocation_not_new_purchase():
    rows={r[0]:r for r in ROWS}
    assert rows['MG996R'][1]==4
    assert rows['MG90S'][1]==2
    assert sum(Decimal(str(r[1]))*Decimal(r[3]) for r in ROWS if r[3])==Decimal('1135.49')
    assert all(r[3]=='' for r in ROWS if r[0] not in ('MG996R','MG90S'))

def test_fasteners_match_servo_clamp_and_idler_counts():
    rows={r[0]:r for r in ROWS}
    assert rows['M3x16 machine screw'][1]==6*4
    assert rows['M4x12 axle screw'][1]==2
    assert rows['M4 regular hex nut'][1]==2
