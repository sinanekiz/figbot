"""Copy the exact SO101 visual model; preserve source hashes and license."""
import json
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from figbot_lab.common import ROOT, sha256, save_json

source = ROOT.parent / 'figbot/GUNCEL/CAD'
model = source / 'URDF/so101_new_calib.xml'
destination = ROOT / 'virtual-leader/public/robot'
destination.mkdir(parents=True, exist_ok=True)
tree = ET.parse(model).getroot()
files = {'URDF/so101_new_calib.xml': sha256(model)}
for item in tree.findall('asset/mesh'):
    filename = item.attrib['file']
    original = source / 'URDF/assets' / filename
    shutil.copy2(original, destination / filename)
    files['URDF/assets/' + filename] = sha256(original)
    assert sha256(destination / filename) == sha256(original)
shutil.copy2(source / 'LICENSE', destination / 'LICENSE')

def numbers(value):
    return [float(n) for n in value.split()]

def body(element):
    result = {'name': element.attrib['name'],
              'position': numbers(element.get('pos', '0 0 0')),
              'quaternion': numbers(element.get('quat', '1 0 0 0')),
              'visuals': [], 'children': []}
    joint = element.find('joint')
    if joint is not None:
        result['joint'] = {'name': joint.get('name'), 'axis': numbers(joint.get('axis')),
                           'range': numbers(joint.get('range'))}
    for geom in element.findall('geom'):
        if geom.get('class') != 'visual':
            continue
        result['visuals'].append({'mesh': geom.get('mesh') + '.stl',
                                 'position': numbers(geom.get('pos', '0 0 0')),
                                 'quaternion': numbers(geom.get('quat', '1 0 0 0')),
                                 'motor': geom.get('mesh').startswith('sts3215')})
    result['children'] = [body(child) for child in element.findall('body')]
    return result

save_json(destination / 'model.json', body(tree.find('worldbody/body')))
save_json(destination / 'provenance.json', {'source_root': str(source), 'files': files,
          'license': 'Apache-2.0', 'geometry_modified': False,
          'note': 'MuJoCo visual hierarchy only; no physical collision or calibration claim.'})
print('SO101 model copied with SHA256 verification:', destination)
