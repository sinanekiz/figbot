"""Slice every distinct part offline; never send generated G-code to a machine."""
import hashlib,json,re,subprocess,zipfile
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from cad.prototype_arm import build_forma_v6 as a


def main():
    exe=next((a.ROOT/'tools/prusaslicer_portable').rglob('prusa-slicer-console.exe'))
    dest=a.ROOT/'.codex_artifacts/FORMA_V6_OFFLINE_NOT_FOR_PRINTER';dest.mkdir(parents=True,exist_ok=True)
    config=dest/'GENERIC_NOT_MACHINE_PROFILE.ini'
    config.write_text('\n'.join([
        'layer_height = 0.2','first_layer_height = 0.2','nozzle_diameter = 0.4',
        'filament_diameter = 1.75','filament_density = 1.24','perimeters = 5',
        'top_solid_layers = 6','bottom_solid_layers = 6','fill_density = 30%',
        'fill_pattern = rectilinear','support_material = 1','support_material_auto = 1',
        'support_material_threshold = 45','support_material_style = snug',
        'support_material_contact_distance = 0.2','support_material_interface_layers = 2',
        'skirts = 0','brim_width = 4','bed_shape = 0x0,256x0,256x256,0x256',
        'max_print_height = 256','gcode_flavor = marlin2','perimeter_generator = arachne','']),encoding='utf-8')
    manifest=json.loads((a.OUT/'MANIFEST.json').read_text())
    def run(row):
        f=a.OUT/'3MF'/(row['part']+'.3mf');target=dest/(f.stem+'.gcode')
        with zipfile.ZipFile(f) as z:
            original=ET.fromstring(z.read('Metadata/Slic3r_PE_model.config'))
            original_modifier_count=len(original.findall(".//metadata[@value='ParameterModifier']"))
        p=subprocess.run([str(exe),'--export-gcode','--dont-arrange','--load',str(config),
             '--output',str(target),str(f)],capture_output=True,creationflags=0x08000000)
        log=p.stdout.decode(errors='replace')+'\n'+p.stderr.decode(errors='replace')
        (dest/(f.stem+'.log')).write_text(log,encoding='utf-8')
        code=target.read_text(errors='replace') if target.exists() else ''
        mass=re.search(r'; filament used \[g\] = ([0-9.]+)',code)
        rt=dest/(f.stem+'_roundtrip.3mf')
        p2=subprocess.run([str(exe),'--export-3mf','--output',str(rt),str(f)],capture_output=True,creationflags=0x08000000)
        modifiers=[];repairs=[]
        if rt.exists():
            with zipfile.ZipFile(rt) as z:root=ET.fromstring(z.read('Metadata/Slic3r_PE_model.config'))
            for v in root.findall('.//volume'):
                md={x.get('key'):x.get('value') for x in v.findall('metadata')}
                if md.get('volume_type')=='ParameterModifier':modifiers.append(md)
                repairs.append(dict(v.find('mesh').attrib))
        rowout={'part':row['part'],'input_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),
            'returncode':p.returncode,'roundtrip_returncode':p2.returncode,
            'modifiers_preserved':len(modifiers)==original_modifier_count and all(m.get('fill_density')=='100%' and m.get('perimeters')=='7' for m in modifiers),
            'support_sections':code.count(';TYPE:Support material'),
            'filament_g_generic_including_support':float(mass[1]) if mass else None,
            'warnings':[l for l in log.splitlines() if any(w in l.lower() for w in ['warning','loose','error','outside'])],
            'mesh_repairs':repairs,
            'statistics':[l for l in code.splitlines() if l.startswith('; estimated printing time')]}
        print(json.dumps(rowout),flush=True);return rowout
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,manifest))
    report={'scope':'PrusaSlicer 2.8.1 generic 0.4 nozzle/0.2 layer/256 bed; not a printer or TPU material profile',
        'printer_commands_sent':False,'physical_print_validated':False,'results':results}
    (a.OUT/'OFFLINE_SLICE_AUDIT.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    assert len(results)==len(a.PARTS) and all(r['returncode']==0 and r['roundtrip_returncode']==0 and r['modifiers_preserved'] and not r['warnings'] for r in results)


if __name__=='__main__':main()
