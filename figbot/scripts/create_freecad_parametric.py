"""Run under FreeCADCmd or FreeCAD GUI to create the native edit documents."""
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'cad/freecad'))
import FreeCAD as App
from figbot_freecad import create_document

out=ROOT/'cad/freecad'
for mode in ('arm','rover','arm_v3','rover_v3'):
    doc=create_document(ROOT,mode,out/'variants'/('baseline_'+mode))
    file=out/('FIGBOT_'+mode.upper()+'_PARAMETRIC.FCStd')
    doc.recompute()
    doc.saveAs(str(file))
    count=len([o for o in doc.Objects if hasattr(o,'Shape')])
    App.closeDocument(doc.Name)
    reopened=App.openDocument(str(file))
    assert reopened.Dimensions.Proxy is not None
    assert reopened.Dimensions.UpperLength.Value==300
    assert all(o.Shape.isValid() for o in reopened.Objects if hasattr(o,'Shape'))
    App.closeDocument(reopened.Name)
    print('PASS saved/reopened',file,'parts',count,flush=True)
