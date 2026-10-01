"""Offline slicing only. G-code is deliberately NOT included in user print packs."""
from pathlib import Path
import subprocess,json,re,hashlib
from cad.prototype_arm.build_breakaway_v4 import OUT,ROOT

def main():
 exe=next((ROOT/'tools/prusaslicer_portable').rglob('prusa-slicer-console.exe'))
 out=OUT/'QA_ONLY_NOT_FOR_PRINTER';out.mkdir(exist_ok=True)
 cfg=out/'offline.ini'
 cfg.write_text("layer_height = 0.2\nfirst_layer_height = 0.2\nnozzle_diameter = 0.4\nfilament_diameter = 1.75\nperimeters = 5\ntop_solid_layers = 5\nbottom_solid_layers = 5\nfill_density = 30%\nfill_pattern = gyroid\nsupport_material = 0\nskirts = 0\nbrim_width = 5\nbed_shape = 0x0,256x0,256x256,0x256\nmax_print_height = 256\ngcode_flavor = marlin2\nperimeter_generator = arachne\noutput_filename_format = offline.gcode\n")
 results=[]
 for f in sorted((OUT/'TABLALAR').glob('*.3mf')):
  target=out/(f.stem+'.gcode')
  p=subprocess.run([str(exe),'--export-gcode','--dont-arrange','--load',str(cfg),'--output',str(target),str(f)],capture_output=True,creationflags=0x08000000)
  log=p.stdout.decode(errors='replace')+'\n'+p.stderr.decode(errors='replace');(out/(f.stem+'.log')).write_text(log)
  lines=log.splitlines();warnings=[l for l in lines if any(s in l.lower() for s in ['warning','overhang','loose','bridging','fragile','consider'])]
  stats=[]
  if target.exists():stats=[l for l in target.read_text(errors='replace').splitlines() if l.startswith(('; filament used [g]','; estimated printing time'))]
  results.append({'file':f.name,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'returncode':p.returncode,'warnings':warnings,'slicer_stats':stats})
  print(f.name,p.returncode,warnings,stats,flush=True)
 (OUT/'OFFLINE_SLICE_AUDIT.json').write_text(json.dumps({'engine':'PrusaSlicer2.8.1 Arachne, offline generic geometry QA; NOT Elegoo printer G-code','config_sha256':hashlib.sha256(cfg.read_bytes()).hexdigest(),'results':results},indent=2))
 assert all(r['returncode']==0 for r in results)
if __name__=='__main__':main()
