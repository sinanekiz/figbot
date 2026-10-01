"""Export and re-import exact STEP without changing any print geometry."""
import json
import cadquery as cq
from cad.prototype_arm import build_aero_v5 as a
from cad.prototype_arm.validate_aero_v5 import vehicle,TARGETS


def verify(path,volume):
    solids=cq.importers.importStep(str(path)).solids().vals()
    actual=sum(s.Volume() for s in solids)
    return {'file':path.relative_to(a.OUT).as_posix(),'solids':len(solids),
        'positive_valid':bool(solids) and all(s.Volume()>0 and s.isValid() for s in solids),
        'relative_volume_error':abs(actual-volume)/volume}


def main():
    report={'parts':[],'assemblies':[],'write_pcurves':False}
    for pid,(fn,_,_) in a.PARTS.items():
        s=fn();p=a.OUT/'PART_STEP'/(pid+'.step')
        cq.exporters.export(s,str(p),opt={'write_pcurves':False})
        row=verify(p,s.val().Volume());report['parts'].append(row);print(row,flush=True)
    for name,items in [('AERO_V5_ASSEMBLY',a.assembly()),
        ('ROVER_PICKUP_REVIEW',vehicle()+a.assembly(a.solve(TARGETS['pickup']),True)),
        ('ROVER_RELEASE_REVIEW',vehicle()+a.assembly(a.solve(TARGETS['release']),True))]:
        assy=cq.Assembly(name=name)
        for k,i in enumerate(items):
            shape=i.shape.val()
            assy.add(shape.located(cq.Location()),loc=shape.location(),name=f'{k:03}_{i.name}'.replace(' ','_'),color=cq.Color(*i.color))
        p=a.OUT/(name+'.step');assy.save(str(p),write_pcurves=False)
        row=verify(p,sum(i.shape.val().Volume() for i in items))
        report['assemblies'].append(row);print(row,flush=True)
    report['passed']=all(r['positive_valid'] and r['relative_volume_error']<1e-4 for r in report['parts']+report['assemblies'])
    (a.OUT/'STEP_ROUNDTRIP.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    assert report['passed']


if __name__=='__main__':main()
