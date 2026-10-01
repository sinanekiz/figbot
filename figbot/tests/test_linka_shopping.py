import json
from scripts import build_linka_shopping as shopping


def test_accepted_bearings_match_current_cad_counts():
    rows = {r['code']: r for r in shopping.ROWS}
    assert rows['B625']['required'] == 2
    assert rows['BALL8']['required'] == 24
    for code in ('B625', 'BALL8'):
        assert not rows[code]['order_hold']
        assert rows[code]['buy_quantity'] >= rows[code]['required']


def test_generated_budget_is_partial_and_separates_currencies(tmp_path, monkeypatch):
    monkeypatch.setattr(shopping, 'OUT', tmp_path)
    shopping.build()
    cost = json.loads((tmp_path / 'MALIYET.json').read_text(encoding='utf-8'))
    assert cost['total_try'] is None
    assert cost['shipping'] is None
    assert cost['machining'] is None
    assert cost['known_subtotals'] == {'USD': 10.05, 'TRY': 215.71}
    assert {'ELBOW_AXLE', 'ELBOW_SLEEVES', 'ROD_BUSH', 'W3'} <= set(cost['excluded'])
    assert not {'B625', 'BALL8'} & set(cost['excluded'])
    doc = (tmp_path / 'SATIN_ALMA_LISTESI.md').read_text(encoding='utf-8')
    assert '| 625ZZ' in doc
    assert '| Ø8 mm çelik bilye' in doc
    assert 'L1.1' in doc
    assert 'YALNIZ önkol' in doc
    assert 'ISO7379-4-M3-6' not in doc
    assert 'M3×10 metal vida' in doc


def test_assembly_fastener_counts_and_candidate_quantities():
    rows = {r['code']: r for r in shopping.ROWS}
    assert len(rows) == len(shopping.ROWS)
    expected = {'I35': 30, 'I34': 2, 'I24': 23, 'I23': 6,
                'S36':16, 'S38': 2, 'S310': 10, 'S320': 4, 'S26': 24, 'S28': 4,
                'W3':32,'W2':6,'W5':2}
    for code, count in expected.items():
        assert rows[code]['required'] == count
        assert rows[code]['buy_quantity'] >= count
    assert all(r['url'] is None or r['url'].startswith('https://') for r in rows.values())
