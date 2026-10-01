"""FreeCAD FeaturePython proxy. Loaded by the FIGBOT user module at startup."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

import FreeCAD as App
import Part

from cad.freecad.parameters import PARAMETERS


def request_for(obj):
    return {'mode':obj.ModelKind,'parameters':{k:float(getattr(obj,k).Value) for k in PARAMETERS}}


def signature(request):
    return hashlib.sha256(json.dumps(request,sort_keys=True).encode()).hexdigest()


def apply_manifest(obj, directory):
    report=json.loads((directory/'manifest.json').read_text(encoding='utf-8'))
    # Read and validate the complete replacement before mutating the document.
    staged=[]
    for item in report['parts']:
        shape=Part.Shape()
        shape.read(str(directory/item['brep']))
        if shape.isNull() or not shape.isValid() or not shape.Solids:
            raise ValueError('Invalid imported part: '+item['name'])
        if abs(shape.Volume-item['volume'])>max(.01,item['volume']*1e-7):
            raise ValueError('Import volume mismatch: '+item['name'])
        staged.append((item,shape))
    doc=obj.Document
    groups={}
    for item,shape in staged:
        group_name='Group_'+item['group'].replace(' ','_')
        group=groups.get(group_name) or doc.getObject(group_name)
        if group is None:
            group=doc.addObject('App::DocumentObjectGroup',group_name)
            group.Label=item['group']
        groups[group_name]=group
        part=doc.getObject(item['id'])
        if part is None:
            part=doc.addObject('Part::Feature',item['id'])
            part.addProperty('App::PropertyString','ComponentKind','FIGBOT')
            part.addProperty('App::PropertyString','PrintStatus','FIGBOT')
            group.addObject(part)
        part.Label=item['name']
        part.Shape=shape
        part.ComponentKind=item['group']
        part.PrintStatus='Generated variant: recheck before print; reference motors/hardware must not be printed'
        if App.GuiUp:
            part.ViewObject.ShapeColor=tuple(item['color'])
            part.ViewObject.LineColor=(.18,.18,.18)
    obj.LastGenerated=signature(request_for(obj))
    obj.ExportDirectory=str(directory)
    obj.BuildState='OK - regenerated geometry; '+('V3 variant requires geometric recheck before print' if obj.ModelKind.endswith('_v3') else 'DEC-039 HOLD still applies')


class ParametricModel:
    def __init__(self,obj):
        self.busy=False
        obj.Proxy=self

    def execute(self,obj):
        if self.busy or not obj.Repository:
            return
        request=request_for(obj)
        if signature(request)==obj.LastGenerated:
            if obj.BuildState.startswith('FAILED'):
                obj.BuildState='OK - previous generated dimensions restored; physical validation required'
            return
        self.busy=True
        try:
            root=Path(obj.Repository)
            python=root/'.venv/Scripts/python.exe'
            if not python.is_file():
                raise RuntimeError('FIGBOT CadQuery environment not found. Restore Repository path.')
            out=Path(tempfile.mkdtemp(prefix=obj.ModelKind+'_',dir=root/'cad/freecad/variants'))
            (out/'request.json').write_text(json.dumps(request),encoding='utf-8')
            obj.BuildState='Building geometry and exports; please wait'
            env=os.environ.copy()
            # FreeCAD bundles its own Python/Qt; do not leak them into CadQuery.
            env.pop('PYTHONHOME',None)
            env.pop('PYTHONPATH',None)
            result=subprocess.run([str(python),'-m','cad.freecad.variant_worker','--request',str(out/'request.json'),'--output',str(out)],cwd=str(root),env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=240,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            (out/'build.log').write_text(result.stdout+'\n'+result.stderr,encoding='utf-8')
            if result.returncode:
                raise RuntimeError('Generation failed. See '+str(out/'build.log'))
            apply_manifest(obj,out)
        except Exception as exc:
            obj.BuildState='FAILED - old geometry retained; '+str(exc)
            App.Console.PrintError(obj.BuildState+'\n')
            raise
        finally:
            self.busy=False

    def onDocumentRestored(self,obj):
        self.busy=False

    def dumps(self):
        return None

    def loads(self,state):
        self.busy=False


def create_document(root,mode,directory):
    report=json.loads((directory/'manifest.json').read_text(encoding='utf-8'))
    doc=App.newDocument('FIGBOT_'+mode.upper()+'_PARAMETRIC')
    doc.Label='FIGBOT '+mode+' - PARAMETRIC / PROTOTYPE'
    obj=doc.addObject('App::FeaturePython','Dimensions')
    obj.Label='00 - OLCULER (Data sekmesinden duzenle)'
    obj.addProperty('App::PropertyString','Repository','Setup')
    obj.Repository=str(root)
    obj.addProperty('App::PropertyString','ModelKind','Setup')
    obj.ModelKind=mode
    obj.setEditorMode('ModelKind',1)
    for key,(_,low,high,unit,description) in PARAMETERS.items():
        kind='App::PropertyAngle' if unit=='deg' else 'App::PropertyLength'
        obj.addProperty(kind,key,'Olculer',description+f' | modelling range {low}..{high}; NOT safety limits')
        setattr(obj,key,report['parameters'][key])
        if mode.startswith('arm') and key not in ('UpperLength','ForeLength'):
            obj.setEditorMode(key,2)
    for key in ('LastGenerated','ExportDirectory','BuildState','Warning'):
        obj.addProperty('App::PropertyString',key,'Status')
        obj.setEditorMode(key,1)
    obj.Warning=('AERO V3: dimensional edits invalidate the baseline geometry audit. Recheck contacts and motion. Physical fit, torque, motor calibration and safety UNVERIFIED. Custom generated features, not independent sketches.' if mode.endswith('_v3') else 'DEC-039: J1 gap, jaw collisions, horn and tube interfaces UNRESOLVED. No print approval. Custom generated features; not independent sketch history.')
    apply_manifest(obj,directory)
    ParametricModel(obj)
    doc.recompute()
    return doc
