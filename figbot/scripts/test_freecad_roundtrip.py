"""Native FreeCAD integration test, including regeneration after reopen."""
import json
from pathlib import Path
import tempfile
import FreeCAD as App

ROOT=Path(__file__).resolve().parents[1]
report={}
for mode,key,value in (('arm','UpperLength',310.),('rover','BasketSlope',10.),('arm_v3','UpperLength',310.),('rover_v3','BasketSlope',10.)):
    source=ROOT/'cad/freecad'/('FIGBOT_'+mode.upper()+'_PARAMETRIC.FCStd')
    doc=App.openDocument(str(source))
    assert doc.Dimensions.Proxy is not None, 'Proxy not restored by installed module'
    before={o.Name:o.Shape.Volume for o in doc.Objects if hasattr(o,'Shape')}
    setattr(doc.Dimensions,key,value)
    doc.recompute()
    assert doc.Dimensions.BuildState.startswith('OK'), doc.Dimensions.BuildState
    manifest=json.loads((Path(doc.Dimensions.ExportDirectory)/'manifest.json').read_text())
    assert manifest['parameters'][key]==value
    changed=[o.Name for o in doc.Objects if hasattr(o,'Shape') and abs(o.Shape.Volume-before[o.Name])>.01]
    if mode.startswith('arm'):
        assert changed, 'Parameter edit did not change actual geometry'
    else:
        floor=next(o for o in doc.Objects if o.Label.startswith('basket floor'))
        import math
        assert abs(floor.Shape.BoundBox.ZMax-(145+600*math.tan(math.radians(10))+6))<.001
    temp=ROOT/'.codex_artifacts'/('freecad_roundtrip_'+mode+'.FCStd')
    doc.saveAs(str(temp))
    App.closeDocument(doc.Name)
    reopened=App.openDocument(str(temp))
    assert getattr(reopened.Dimensions,key).Value==value
    assert all(o.Shape.isValid() for o in reopened.Objects if hasattr(o,'Shape'))
    report[mode]={'parameter':key,'tested_value':value,'changed_volume_parts':changed,'valid_after_reopen':True}
    App.closeDocument(reopened.Name)
(ROOT/'cad/freecad/NATIVE_TEST_REPORT.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('PASS native reopen -> edit -> regenerate -> save -> reopen',flush=True)
