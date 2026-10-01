"""CadQuery side of FreeCAD bridge. Never overwrite controlled Rev-H exports."""
import argparse
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

import cadquery as cq
import numpy as np
from cad.freecad.parameters import DEFAULTS, validate
from cad.prototype_arm import build_aero_v2 as arm
from cad.rover import build_rev_h_review as rover

HOLD = 'DEC-039 HOLD: assembly defects retained; NOT FOR PRINT / PHYSICAL VALIDATION REQUIRED'


def configure(values):
    p = validate(values)
    arm.UPPER_LINK_LENGTH = p['UpperLength']
    arm.FOREARM_LINK_LENGTH = p['ForeLength']
    rover.BASE = (p['ArmBaseX'], p['ArmBaseY'], p['ArmBaseZ'])
    rover.SLOPE = p['BasketSlope']
    rover.BASKET_REAR_Z = p['BasketRearHeight']
    rover.vehicle.cache_clear()
    rover.reference_components.cache_clear()
    return p


def reference_arm():
    """Adapt cosmetic sleeves to changed spans; preserve exact default geometry."""
    result = []
    upper, fore = arm.UPPER_LINK_LENGTH, arm.FOREARM_LINK_LENGTH
    shoulder = (0., 0., arm.ASSEMBLY_SHOULDER_Z)
    elbow = (upper*math.cos(math.radians(18)), 0., shoulder[2]-upper*math.sin(math.radians(18)))
    for c in arm.assembly_components():
        shape = c.shape
        if c.name.startswith('upper hollow fairing') and upper != DEFAULTS['UpperLength']:
            i = int(c.name.rsplit(' ', 1)[1])-1
            shape = arm._place(arm.fairing_module(94*upper/300).translate(((52,150,248)[i]*upper/300,0,0)), shoulder, 18)
        elif c.name.startswith('forearm hollow fairing') and fore != DEFAULTS['ForeLength']:
            i = int(c.name.rsplit(' ', 1)[1])-1
            shape = arm._place(arm.fairing_module(104*fore/220).translate(((55,165)[i]*fore/220,0,0)), elbow, -18)
        result.append(arm.Component(c.name, shape, c.group, c.color))
    return result


def posed_arm(reference, pose, side):
    """Rev-H rigid transforms, replacing its two hardcoded 300 mm spans."""
    yaw, upper, fore = pose
    shoulder = (0., 0., arm.ASSEMBLY_SHOULDER_Z)
    length = arm.UPPER_LINK_LENGTH
    old_e = np.array([length*math.cos(math.radians(18)),0,shoulder[2]-length*math.sin(math.radians(18))])
    new_e = np.array([length*math.cos(math.radians(upper)),0,shoulder[2]-length*math.sin(math.radians(upper))])
    fixed = {'J1 rounded base','J1 yaw deck','open shoulder pedestal','dual-servo shoulder yoke'}
    upper_names = {'upper hub','300 mm aluminium upper tube','adjustable counterbalance tube anchor','elbow yoke','J2 horn'}
    result = []
    for c in reference:
        name, shape = c.name, c.shape
        if name == 'elastic counterbalance reference':
            continue
        if name in fixed or name.startswith(('J1 MG996R','J2L MG996R','J2R MG996R')):
            pass
        elif name in upper_names or name.startswith(('upper hollow','J3 MG996R')):
            shape = shape.rotate(shoulder,(0,1,shoulder[2]),upper-18)
        else:
            shape = shape.rotate(tuple(old_e),tuple(old_e+np.array([0,1,0])),fore+18).translate(tuple(new_e-old_e))
        if name != 'J1 rounded base' and not name.startswith('J1 MG996R'):
            shape = shape.rotate((0,0,0),(0,0,1),yaw*side)
        shape = shape.translate((rover.BASE[0],side*rover.BASE[1],rover.BASE[2]))
        result.append(arm.Component(('L ' if side==1 else 'R ')+name,shape,c.group,c.color))
    return result


def components(mode, values):
    configure(values)
    if mode in ('arm_v3','rover_v3'):
        from cad.prototype_arm import build_aero_v3 as v3
        from cad.prototype_arm.audit_aero_v3 import vehicle as vehicle_v3
        v3.UPPER,v3.FORE=300.,220.
        v3.BASE=(380.,415.,280.)
        baseline=v3.ik(v3.TARGETS['pickup'])
        v3.UPPER,v3.FORE=values['UpperLength'],values['ForeLength']
        v3.BASE=(values['ArmBaseX'],values['ArmBaseY'],values['ArmBaseZ'])
        if mode=='arm_v3':return v3.assembly(baseline,grip=-20,base=v3.BASE)
        parts=vehicle_v3()
        for side in (1,-1):
            pose=(side*baseline[0],baseline[1],baseline[2])
            base=(v3.BASE[0],side*v3.BASE[1],v3.BASE[2])
            for c in v3.assembly(pose,grip=-20,base=base):
                parts.append(v3.Component(('L ' if side==1 else 'R ')+c.name,c.shape,c.group,c.color,c.part_id))
        return parts
    reference = reference_arm()
    if mode == 'arm':
        return reference
    # Keep the current pickup joint pose while exploring dimensions. This is
    # NOT an IK target or motion controller; altered lengths move the tool.
    original_base, original_upper, original_fore = rover.BASE, arm.UPPER_LINK_LENGTH, arm.FOREARM_LINK_LENGTH
    rover.BASE = (380.,415.,280.)
    arm.UPPER_LINK_LENGTH, arm.FOREARM_LINK_LENGTH = 300.,220.
    pose = rover.solve_pose(rover.TARGETS['pickup'])
    rover.BASE = original_base
    arm.UPPER_LINK_LENGTH, arm.FOREARM_LINK_LENGTH = original_upper, original_fore
    return rover.vehicle()+[c for side in (1,-1) for c in posed_arm(reference,pose,side)]


def build(mode, values, output):
    p = validate(values)
    output.mkdir(parents=True, exist_ok=True)
    parts = components(mode,p)
    model = cq.Assembly(name='FIGBOT_FreeCAD_'+mode)
    metadata = []
    for i,c in enumerate(parts):
        shape = c.shape.val()
        if not shape.isValid() or not shape.Solids():
            raise ValueError(f'Invalid or empty solid: {c.name}')
        file = f'part_{i:03d}.brep'
        shape.exportBrep(str(output/file))
        label = c.name.replace('300 mm aluminium upper tube',f'{p["UpperLength"]:g} mm upper span - cut length TBD').replace('220 mm aluminium forearm tube',f'{p["ForeLength"]:g} mm fore span - cut length TBD').replace('basket floor 15deg',f'basket floor {p["BasketSlope"]:g} deg')
        metadata.append({'id':f'Component{i:03d}','name':label,'group':c.group,'color':c.color,'brep':file,'volume':shape.Volume()})
        model.add(c.shape,name=f'{i:03d}_{c.name}',color=cq.Color(*c.color))
    model.save(str(output/'model.step'),exportType='STEP')
    model.save(str(output/'model.glb'),exportType='GLTF',tolerance=.2,angularTolerance=.12)
    compound = cq.Compound.makeCompound([c.shape.val() for c in parts])
    cq.exporters.export(compound,str(output/'scene.stl'),tolerance=.2,angularTolerance=.12)
    robot=ET.Element('robot',name='FIGBOT_FIXED_INSPECTION_NOT_KINEMATIC')
    visual=ET.SubElement(ET.SubElement(robot,'link',name='scene'),'visual')
    ET.SubElement(ET.SubElement(visual,'geometry'),'mesh',filename='scene.stl',scale='0.001 0.001 0.001')
    ET.ElementTree(robot).write(output/'inspection_fixed.urdf',encoding='utf-8',xml_declaration=True)
    # Generic caption to avoid reusing the controlled Rev-H 15-degree caption.
    from cad.utils import render_preview
    render_preview(compound,output/'preview.png','FIGBOT FreeCAD '+mode+' | HOLD / NOT FOR PRINT')
    report = {'mode':mode,'parameters':p,'status':('AERO V3 experimental variant; RECHECK GEOMETRY BEFORE PRINT' if mode.endswith('_v3') else HOLD),'parts':metadata,
              'scope':'Geometry regeneration only; no automatic collision, strength, kinematics or print approval. Fixed pickup joint pose. Imported/custom generated features, not sketch history.'}
    (output/'manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(f'BUILT {mode}: {len(parts)} components',flush=True)
    return report


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--request',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    request=json.loads(Path(args.request).read_text(encoding='utf-8'))
    build(request['mode'],request['parameters'],Path(args.output))
