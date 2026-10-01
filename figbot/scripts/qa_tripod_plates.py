"""Offline generic slicing only. Output G-code stays outside delivery."""
import json,subprocess,hashlib,re
from concurrent.futures import ThreadPoolExecutor
from scripts.project_paths import ROOT,PRINTS,CAD

def main():
    status=json.loads((CAD/'TUTUCU/STATUS.json').read_text())
    if status['revision']=='DEC-086':
        from scripts.package_twin_plates import NEW
    else:
        from scripts.package_tripod_plates import NEW
    dest=ROOT/'.codex_artifacts/TRIPOD_OFFLINE_NOT_FOR_PRINTER';dest.mkdir(parents=True,exist_ok=True)
    exe=next((ROOT/'tools/prusaslicer_portable').rglob('prusa-slicer-console.exe'))
    cfg=dest/'GENERIC_NOT_MACHINE_PROFILE.ini'
    cfg.write_text('\n'.join(['layer_height = 0.16','first_layer_height = 0.2','nozzle_diameter = 0.4','filament_diameter = 1.75','filament_density = 1.24','perimeters = 5','top_solid_layers = 5','bottom_solid_layers = 5','fill_density = 100%','fill_pattern = rectilinear','support_material = 1','support_material_auto = 1','support_material_buildplate_only = 1','support_material_threshold = 45','support_material_style = snug','support_material_contact_distance = 0.2','support_material_interface_layers = 2','skirts = 0','brim_width = 5','bed_shape = 0x0,256x0,256x256,0x256','max_print_height = 256','gcode_flavor = marlin2','perimeter_generator = arachne','']),encoding='utf-8')
    def run(name):
        src=PRINTS/name/(name+'.3mf');gcode=dest/(name+'.gcode')
        p=subprocess.run([str(exe),'--export-gcode','--dont-arrange','--load',str(cfg),'--output',str(gcode),str(src)],capture_output=True,creationflags=0x08000000)
        log=p.stdout.decode(errors='replace')+'\n'+p.stderr.decode(errors='replace');(dest/(name+'.log')).write_text(log,encoding='utf-8')
        code=gcode.read_text(errors='replace') if gcode.exists() else ''
        mass=re.search(r'; filament used \[g\] = ([0-9.]+)',code)
        row=dict(plate=name,returncode=p.returncode,input_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),layer_count=code.count(';LAYER_CHANGE'),support_sections=code.count(';TYPE:Support material'),generic_filament_g_including_support=float(mass[1]) if mass else None,warnings=[l for l in log.splitlines() if any(w in l.lower() for w in ['warning','error','outside','empty'])])
        print(json.dumps(row),flush=True);return row
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,list(NEW)+['09_CUBUK_VE_BURCLAR']))
    report=dict(scope='Generic PrusaSlicer 2.8.1 / 0.4mm nozzle / 0.16mm layer. Not actual Elegoo profile.',printer_commands_sent=False,physical_approval=False,results=results)
    (CAD/'TUTUCU/PRINT_SLICE_AUDIT.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    assert all(r['returncode']==0 and r['layer_count']>5 and not r['warnings'] for r in results)

if __name__=='__main__':main()
