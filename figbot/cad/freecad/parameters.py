"""Editable variant parameters; defaults mirror Rev-H2, not a new release."""
import math

PARAMETERS = {
    'UpperLength': (300., 140., 450., 'mm', 'Omuz-dirsek eksen araligi; metal kesim boyu DEGIL'),
    'ForeLength': (220., 140., 350., 'mm', 'Dirsek-bilek eksen araligi; metal kesim boyu DEGIL'),
    'BasketSlope': (15., 5., 25., 'deg', 'Sepet on yuksek / arka alcak egimi'),
    'BasketRearHeight': (145., 120., 220., 'mm', 'Sepet arka tabaninin yerden yuksekligi'),
    'ArmBaseX': (380., 300., 450., 'mm', 'Iki kol tabaninin ileri konumu'),
    'ArmBaseY': (415., 350., 500., 'mm', 'Kol tabanlarinin merkezden sag/sol mesafesi'),
    'ArmBaseZ': (280., 260., 400., 'mm', 'Kol tabanlarinin yerden yuksekligi'),
}
DEFAULTS = {key: item[0] for key, item in PARAMETERS.items()}


def validate(values):
    if set(values) != set(PARAMETERS):
        raise ValueError('Parameter keys do not match schema')
    result = {}
    for key, (_, low, high, _, _) in PARAMETERS.items():
        value = float(values[key])
        if not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f'{key}: allowed modelling range {low}..{high}; not a safe operating range')
        result[key] = value
    return result
