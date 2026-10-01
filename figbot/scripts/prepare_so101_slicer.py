"""Prepare ECC2 native projects from unchanged SO101 meshes and installed OEM profiles.

This does not communicate with or start a printer. Physical calibration remains separate.
"""
import json
import os
import shutil
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from scripts.package_so101 import PLATES, placed_mesh, ROOT, write_json

WORK = ROOT / '.tmp_artifact/so101_slicing'
PROFILES = Path('C:/Program Files/ElegooSlicer/resources/profiles/Elegoo')
MACHINE = 'Elegoo Centauri Carbon 2 0.4 nozzle'
BASE_PROCESS = '0.20mm Standard @Elegoo CC2 0.4 nozzle'
GENERAL = 'FIGBOT Genel Kalite 0.20 - CC2 0.4'
ARM = 'FIGBOT SO101 PLA+ 0.20 - CC2 0.4'
FILAMENT = 'FIGBOT PLA+ 225C - CC2'
COMMON = dict(layer_height='0.2', initial_layer_print_height='0.2', wall_loops='3',
              top_shell_layers='5', bottom_shell_layers='4', top_shell_thickness='1',
              bottom_shell_thickness='0.8', sparse_infill_density='20%', sparse_infill_pattern='gyroid',
              outer_wall_speed='60', inner_wall_speed='100', sparse_infill_speed='120',
              internal_solid_infill_speed='100', top_surface_speed='50', gap_infill_speed='60',
              initial_layer_speed='30', initial_layer_infill_speed='40', bridge_speed='25',
              default_acceleration='3000', outer_wall_acceleration='1500', top_surface_acceleration='1500',
              initial_layer_acceleration='500', travel_speed='300', travel_acceleration='5000',
              enable_prime_tower='0', enable_support='0', brim_type='auto_brim', brim_width='5',
              brim_object_gap='0.15', top_solid_infill_flow_ratio='1', print_flow_ratio='1',
              support_type='normal(auto)', support_style='snug', support_threshold_angle='45', support_top_z_distance='0.2',
              support_bottom_z_distance='0.2', support_object_xy_distance='0.35',
              support_interface_top_layers='3', support_interface_bottom_layers='2',
              support_interface_spacing='0.3', support_base_pattern_spacing='2.5',
              support_speed='80', support_interface_speed='45', support_on_build_plate_only='0',
              bridge_no_support='1', support_remove_small_overhang='1', skirt_loops='0')
ARM_SETTINGS = {**COMMON, 'wall_loops':'4', 'bottom_shell_layers':'5',
                'bottom_shell_thickness':'1', 'sparse_infill_density':'25%',
                'enable_support':'1', 'brim_type':'outer_only'}
FILAMENT_SETTINGS = dict(nozzle_temperature=['225'], nozzle_temperature_initial_layer=['225'],
    nozzle_temperature_range_low=['210'], nozzle_temperature_range_high=['235'],
    textured_plate_temp=['60'], textured_plate_temp_initial_layer=['60'],
    hot_plate_temp=['60'], hot_plate_temp_initial_layer=['60'], filament_max_volumetric_speed=['10'],
    filament_vendor=['Generic'], filament_flow_ratio=['1'], enable_pressure_advance=['0'],
    filament_notes=['PLA+; user reports 225C successful, label 210-235C; brand unknown. Flow/PA uncalibrated.'],
    additional_cooling_fan_speed=['0'], slow_down_layer_time=['8'])

def resolved(name):
    index={}
    for p in PROFILES.rglob('*.json'):
        d=json.loads(p.read_text(encoding='utf-8')); index[d.get('name')]=d
    def recurse(n):
        d=index[n]; return {**(recurse(d['inherits']) if d.get('inherits') else {}), **d}
    return recurse(name)

def profiles():
    WORK.mkdir(parents=True, exist_ok=True)
    out=WORK/'PROFILLER';out.mkdir(exist_ok=True)
    for name,settings in [(GENERAL,COMMON),(ARM,ARM_SETTINGS)]:
        write_json(out/(name+'.json'), dict(type='process', name=name, inherits=BASE_PROCESS,
            **{'from':'User'}, is_custom_defined='0', print_settings_id=name, version='1.5.3.5',
            compatible_printers=[MACHINE], **settings))
    write_json(out/(FILAMENT+'.json'), dict(type='filament', name=FILAMENT,
        inherits='Elegoo PLA+ @ECC2', **{'from':'User'}, filament_settings_id=[FILAMENT],
        version='1.5.3.5', compatible_printers=[MACHINE], **FILAMENT_SETTINGS))

def settings(arm=True):
    with zipfile.ZipFile(ROOT/'manufacturing/ecc2_slicer_template.3mf') as z:
        d=json.loads(z.read('Metadata/project_settings.config'))
    # Template had three unused material slots. Preserve machine arrays (usually length 2),
    # collapse the observed three-material vectors, then apply resolved PLA settings.
    for k,v in list(d.items()):
        if isinstance(v,list) and len(v)==3:d[k]=v[:1]
    filament=resolved('Elegoo PLA+ @ECC2')
    for k,v in filament.items():
        if k in d:d[k]=v
    d.update(FILAMENT_SETTINGS)
    d.update(ARM_SETTINGS if arm else COMMON)
    d.update(filament_settings_id=[FILAMENT],filament_ids=['FIGBOT_PLA_PLUS'],
             filament_colour=['#408080'], filament_colour_type=['1'], default_filament_colour=['#408080'],
             flush_volumes_matrix=['0'],flush_volumes_vector=['140','140'],
             printer_settings_id=MACHINE, print_settings_id=ARM if arm else GENERAL,
             curr_bed_type='Textured PEI Plate')
    return d

NS='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
def native_project(plate, items):
    folder=WORK/plate;folder.mkdir(exist_ok=True)
    ET.register_namespace('',NS)
    model=ET.Element('model',{'unit':'millimeter','xmlns':NS})
    ET.SubElement(model,'metadata',{'name':'Application'}).text='ElegooSlicer-1.5.3.5'
    ET.SubElement(model,'metadata',{'name':'BambuStudio:3mfVersion'}).text='1'
    resources=ET.SubElement(model,'resources'); build=ET.SubElement(model,'build')
    config=ET.Element('config'); platecfg=ET.Element('plate')
    ET.SubElement(platecfg,'metadata',key='plater_id',value='1')
    ET.SubElement(platecfg,'metadata',key='plater_name',value=plate)
    ET.SubElement(platecfg,'metadata',key='locked',value='false')
    for i,(code,name,x,y) in enumerate(items,1):
        mesh,_=placed_mesh(name,x,y)
        obj=ET.SubElement(resources,'object',id=str(i),type='model',name=code+'_'+name)
        m=ET.SubElement(obj,'mesh');v=ET.SubElement(m,'vertices');f=ET.SubElement(m,'triangles')
        for a,b,c in mesh.vertices:ET.SubElement(v,'vertex',x=f'{a:.7f}',y=f'{b:.7f}',z=f'{c:.7f}')
        for a,b,c in mesh.faces:ET.SubElement(f,'triangle',v1=str(a),v2=str(b),v3=str(c))
        ET.SubElement(build,'item',objectid=str(i),transform='1 0 0 0 1 0 0 0 1 0 0 0',printable='1')
        oc=ET.SubElement(config,'object',id=str(i))
        ET.SubElement(oc,'metadata',key='name',value=code+'_'+name)
        ET.SubElement(oc,'metadata',key='extruder',value='1')
        part=ET.SubElement(oc,'part',id=str(i),subtype='normal_part')
        ET.SubElement(part,'metadata',key='name',value=code+'_'+name)
        inst=ET.SubElement(platecfg,'model_instance')
        for k,val in [('object_id',str(i)),('instance_id','0'),('identify_id',str(i))]:
            ET.SubElement(inst,'metadata',key=k,value=val)
    config.append(platecfg)
    config.append(ET.Element('assemble'))
    cfg=settings()
    if plate.startswith('00_'): cfg.update(enable_support='0',brim_type='no_brim')
    with zipfile.ZipFile(folder/'BASKI_HAZIR.3mf','w',zipfile.ZIP_DEFLATED) as z:
        with zipfile.ZipFile(ROOT/'manufacturing/ecc2_slicer_template.3mf') as t:
            for n in ['[Content_Types].xml','_rels/.rels','Metadata/slice_info.config']:
                z.writestr(n,t.read(n))
        z.writestr('3D/3dmodel.model',ET.tostring(model,encoding='utf-8',xml_declaration=True))
        z.writestr('Metadata/model_settings.config',ET.tostring(config,encoding='utf-8',xml_declaration=True))
        z.writestr('Metadata/project_settings.config',json.dumps(cfg,ensure_ascii=False,indent=2))
    return folder/'BASKI_HAZIR.3mf'

def main():
    profiles()
    for plate,items in PLATES.items():print(native_project(plate,items))

if __name__=='__main__':main()
