"""Check actual ElegooSlicer output; render support/toolpath review sheets, not screenshots."""
import json, re, math
from pathlib import Path
from collections import defaultdict
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from scripts.prepare_so101_slicer import WORK, MACHINE

def parse(path):
    xyz=np.zeros(3); role='Custom'; started=False; segments=[]; counts=defaultdict(float)
    config={}; summary={}
    for line in path.read_text(encoding='utf-8',errors='replace').splitlines():
        if line.startswith(';TYPE:'):role=line[6:]
        if line.startswith(';LAYER_CHANGE'):started=True
        if line.startswith(';') and ' = ' in line:
            k,v=line[1:].split(' = ',1);config[k.strip()]=v.strip()
        if not started or not line.startswith(('G0 ','G1 ')):continue
        words=dict((a,float(b)) for a,b in re.findall(r'([XYZEF])(-?\d*\.?\d+)',line))
        nxt=xyz.copy()
        for i,axis in enumerate('XYZ'):
            if axis in words:nxt[i]=words[axis]
        if words.get('E',0)>0 and np.linalg.norm(nxt[:2]-xyz[:2])>0.0001 and role!='Custom':
            segments.append((xyz.copy(),nxt.copy(),role))
            counts[role]+=words['E']
        xyz=nxt
    return segments,config,counts

def audit(folder):
    segments,c,counts=parse(folder/'plate_1.gcode')
    pts=np.array([s[1] for s in segments]);low=pts.min(axis=0);high=pts.max(axis=0)
    assert c['printer_settings_id']==MACHINE
    assert c['nozzle_temperature']=='225' and c['nozzle_diameter']=='0.4'
    assert c['wall_loops']=='4' and c['sparse_infill_density']=='25%'
    assert c['curr_bed_type']=='Textured PEI Plate'
    assert np.all(low>=0) and np.all(high<256), (low,high)
    assert not np.any((pts[:,0]>=246)&(pts[:,1]<=20)), 'reserved purge area'
    assert 'Potentially lost branch' not in (folder/'cli.log').read_text()
    bridges=[np.linalg.norm(b[:2]-a[:2]) for a,b,r in segments if r=='Bridge']
    total=sum(counts.values());support=sum(v for k,v in counts.items() if k.startswith('Support'))
    result=dict(plate=folder.name,segments=len(segments),extrusion_bounds_mm=[low.tolist(),high.tolist()],
        estimated_time=c.get('estimated printing time (normal mode)'),filament_g=float(c['total filament used [g]']),
        support_filament_fraction=support/total, max_bridge_segment_mm=max(bridges,default=0),
        geometry_and_calibration_physical_validation=False)
    fig,axs=plt.subplots(2,3,figsize=(15,10))
    heights=[.2,1,5,15,30,min(60,high[2])]
    for ax,z in zip(axs.ravel(),heights):
        model=[];supp=[];bridge=[]
        for a,b,r in segments:
            if abs(b[2]-z)>.11:continue
            target=supp if r.startswith('Support') else bridge if r=='Bridge' else model
            target.append([a[:2],b[:2]])
        for data,col in [(model,'#234957'),(supp,'#1cb649'),(bridge,'#e37e27')]:
            ax.add_collection(LineCollection(data,colors=col,linewidths=.4))
        ax.set(xlim=(0,256),ylim=(0,256),aspect='equal',title=f'Z = {z:.1f} mm');ax.grid(alpha=.15)
    fig.suptitle(folder.name+' | model: blue, support: green, bridge: orange')
    fig.tight_layout();fig.savefig(folder/'KATMAN_KONTROL.png',dpi=150);plt.close(fig)
    (folder/'KONTROL.json').write_text(json.dumps(result,indent=2))
    return result

if __name__=='__main__':
    print(json.dumps([audit(p) for p in WORK.iterdir() if p.is_dir() and (p/'plate_1.gcode').exists()],indent=2))
