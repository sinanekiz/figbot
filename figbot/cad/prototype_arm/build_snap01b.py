"""Correct only the slider insertion path; no functional torque coupling claim."""
from functools import lru_cache
import json,shutil,zipfile
import cadquery as cq
from cad.prototype_arm import build_snap01 as old

OUT=old.OUT/'REV_B'

@lru_cache(None)
def build():
    body,lid=old.build()
    # +Y is the leading edge when inserting the lid from the body's -Y entrance.
    # Open the existing 14mm hole to that edge so a protruding hub can enter it.
    lid=lid.cut(old.box(14,22,4,(0,11,1)))
    return body,lid

def main():
    old.main(OUT,build,{'revision':'B - open leading U slot',
        'reason':'Old closed aperture collided with protruding horn hub during sliding assembly',
        'body_changed':False,'slot_width_mm':14,
        'hub_test_envelopes_mm':[8,10,12,13.5],
        'hub_test_note':'Artificial regression envelopes, NOT measurements of user hardware. Real fit and torque transfer still unverified.'})
    shutil.copy2(OUT/'PRINT/SNAP01_02_KAPAK.stl',OUT/'SNAP01B_SADECE_KAPAK.stl')
    with zipfile.ZipFile(OUT/'SNAP01B_SADECE_KAPAK.zip','w',zipfile.ZIP_DEFLATED) as z:
        for n in ['SNAP01B_SADECE_KAPAK.stl','ONCE_OKU.md','AUDIT.json','MONTAJ_ONIZLEME.png']:
            z.write(OUT/n,n)

if __name__=='__main__':main()
