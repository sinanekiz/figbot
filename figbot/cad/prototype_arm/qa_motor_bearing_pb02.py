"""Generic offline support check; generated G-code is NOT FOR THE PRINTER."""
import json,hashlib,subprocess
from cad.prototype_arm.build_motor_bearing_pb02 import ROOT,OUT

def main():
    exe=next((ROOT/'tools/prusaslicer_portable').rglob('prusa-slicer-console.exe'))
    folder=ROOT/'.codex_artifacts/PB02_OFFLINE_NOT_FOR_PRINTER';folder.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((OUT/'MANIFEST.json').read_text());results=[]
    for plate in manifest['plates']:
        f=OUT/plate['file'];balls=f.name.startswith('05_');config=folder/(f.stem+'.ini')
        config.write_text('\n'.join([
            f'layer_height = {0.12 if balls else 0.16}','first_layer_height = 0.2',
            'nozzle_diameter = 0.4','filament_diameter = 1.75','filament_density = 1.24',
            'perimeters = 4','top_solid_layers = 5','bottom_solid_layers = 5',
            f'fill_density = {100 if balls else 30}%',f'fill_pattern = {"rectilinear" if balls else "gyroid"}',
            'support_material = 1','support_material_auto = 1','support_material_threshold = 45',
            'support_material_style = snug',f'support_material_enforce_layers = {34 if balls else 0}',
            f'support_material_buildplate_only = {1 if balls else 0}',
            'support_material_contact_distance = 0.16','support_material_interface_layers = 2',
            'skirts = 0','brim_width = 5','bed_shape = 0x0,256x0,256x256,0x256',
            'max_print_height = 256','gcode_flavor = marlin2','perimeter_generator = arachne','']),encoding='utf-8')
        target=folder/(f.stem+'.gcode')
        if target.exists():target.unlink()
        p=subprocess.run([str(exe),'--export-gcode','--dont-arrange','--load',str(config),'--output',str(target),str(f)],capture_output=True,creationflags=0x08000000)
        log=p.stdout.decode(errors='replace')+'\n'+p.stderr.decode(errors='replace')
        (folder/(f.stem+'.log')).write_text(log,encoding='utf-8')
        code=target.read_text(errors='replace') if target.exists() else ''
        r={'file':f.name,'input_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'returncode':p.returncode,
           'support_sections':code.count(';TYPE:Support material'),
           'warnings':[l for l in log.splitlines() if any(w in l.lower() for w in ['warning','loose','error','outside'])],
           'statistics':[l for l in code.splitlines() if l.startswith(('; filament used [g]','; estimated printing time'))]}
        results.append(r);print(json.dumps(r),flush=True)
    (OUT/'OFFLINE_SLICE_AUDIT.json').write_text(json.dumps({'scope':'PrusaSlicer 2.8.1 GENERIC OFFLINE; NOT Elegoo machine profile','printer_commands_sent':False,'physical_print_validated':False,'results':results},indent=2))
    assert len(results)==5 and all(r['returncode']==0 and r['support_sections']>0 and not r['warnings'] for r in results)

if __name__=='__main__':main()
