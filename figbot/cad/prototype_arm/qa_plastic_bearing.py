"""Offline support-generation check. Never send these generic files to a printer."""
import hashlib
import json
import subprocess
import argparse
from cad.prototype_arm.build_plastic_bearing import ROOT, OUT, SMALL, LARGE


def main(spec=SMALL):
    exe=next((ROOT/'tools/prusaslicer_portable').rglob('prusa-slicer-console.exe'))
    folder=ROOT/'.codex_artifacts/PB01_OFFLINE_NOT_FOR_PRINTER'/spec.name
    folder.mkdir(parents=True,exist_ok=True)
    results=[]
    for f in sorted((OUT/spec.name).glob('*.3mf')):
        balls=f.name.startswith('BILYELER')
        config=folder/(f.stem+'.ini')
        config.write_text('\n'.join([
            f'layer_height = {0.12 if balls else 0.16}','first_layer_height = 0.2',
            'nozzle_diameter = 0.4','filament_diameter = 1.75','filament_density = 1.24',
            'perimeters = 4','top_solid_layers = 5','bottom_solid_layers = 5',
            f'fill_density = {100 if balls else 30}%',
            f'fill_pattern = {"rectilinear" if balls else "gyroid"}',
            'support_material = 1','support_material_auto = 1','support_material_threshold = 45',
            'support_material_style = snug',
            f'support_material_enforce_layers = {34 if balls else 0}',
            f'support_material_buildplate_only = {1 if balls else 0}',
            'support_material_contact_distance = 0.16','support_material_interface_layers = 2',
            'skirts = 0','brim_width = 5','bed_shape = 0x0,256x0,256x256,0x256',
            'max_print_height = 256','gcode_flavor = marlin2','perimeter_generator = arachne',
            'output_filename_format = offline.gcode','']),encoding='utf-8')
        target=folder/(f.stem+'.gcode')
        # Never inspect a stale output if a new slice fails before writing it.
        if target.exists():target.unlink()
        p=subprocess.run([str(exe),'--export-gcode','--dont-arrange','--load',str(config),
                          '--output',str(target),str(f)],capture_output=True,creationflags=0x08000000)
        log=p.stdout.decode(errors='replace')+'\n'+p.stderr.decode(errors='replace')
        (folder/(f.stem+'.log')).write_text(log,encoding='utf-8')
        code=target.read_text(errors='replace') if target.exists() else ''
        supports=code.count(';TYPE:Support material')
        result={'file':f.name,'input_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),
                'returncode':p.returncode,'support_sections':supports,
                'warnings':[l for l in log.splitlines() if any(w in l.lower() for w in ['warning','loose','error','outside'])],
                'statistics':[l for l in code.splitlines() if l.startswith(('; filament used [g]','; estimated printing time'))]}
        results.append(result);print(json.dumps(result),flush=True)
    report={'scope':'PrusaSlicer 2.8.1 GENERIC OFFLINE CHECK; NOT Elegoo machine profile',
            'printer_commands_sent':False,'physical_print_validated':False,'results':results}
    report['variant']=spec.name
    name='OFFLINE_SLICE_AUDIT.json' if spec==SMALL else 'LARGE_OFFLINE_SLICE_AUDIT.json'
    (OUT/name).write_text(json.dumps(report,indent=2),encoding='utf-8')
    assert all(r['returncode']==0 for r in results)
    assert next(r for r in results if r['file'].startswith('BILYELER'))['support_sections']>0


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--large',action='store_true')
    args=parser.parse_args();main(LARGE if args.large else SMALL)
