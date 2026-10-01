"""Offline joint-space route proposals with explicit open-before-approach stages.

Candidates follow demonstrated joint corridors. No collision model or hardware
control is included; these are NOT executable robot plans.
"""
import argparse
import json
from pathlib import Path
import numpy as np


def simplify(points, tolerance=32.):
    """RDP using max per-joint deviation from the endpoint line segment."""
    p=np.asarray(points,dtype=float)
    if len(p)<=2:return p.copy()
    delta=p[-1]-p[0];den=float(delta@delta)
    u=np.clip((p-p[0])@delta/den,0,1) if den else np.zeros(len(p))
    error=abs(p-(p[0]+u[:,None]*delta)).max(axis=1)
    i=int(error.argmax())
    if error[i]<=tolerance:return p[[0,-1]].copy()
    return np.concatenate([simplify(p[:i+1],tolerance)[:-1],simplify(p[i:],tolerance)])


def smooth_segments(points, velocity, acceleration, dt=.02):
    """Rest-to-rest quintic segments; analytic velocity/acceleration bounds."""
    if velocity<=0 or acceleration<=0:raise ValueError('Positive proposal limits required')
    p=np.asarray(points,dtype=float);samples=[p[0]];times=[0.]
    for a,b in zip(p[:-1],p[1:]):
        extent=float(abs(b-a).max())
        if extent<.01:continue
        duration=max(1.875*extent/velocity,np.sqrt(5.773503*extent/acceleration),dt)
        u=np.linspace(0,1,int(np.ceil(duration/dt))+1)[1:]
        s=10*u**3-15*u**4+6*u**5
        samples.extend(a+s[:,None]*(b-a));times.extend(times[-1]+duration*u)
    return np.asarray(times),np.asarray(samples)


def blended_segments(points, velocity, acceleration, dt=.02):
    """PCHIP corridor with curvature-aware forward/backward time parameterization.

    Bounds are numerical offline checks, not measured servo performance.
    """
    from scipy.interpolate import PchipInterpolator
    p=np.asarray(points,dtype=float)
    p=p[np.r_[True,np.linalg.norm(np.diff(p,axis=0),axis=1)>.01]]
    if len(p)<3:return smooth_segments(p,velocity,acceleration,dt)
    knots=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
    curve=PchipInterpolator(knots,p,axis=0)
    s=np.linspace(0,knots[-1],max(200,int(knots[-1]/2)+1))
    path=curve(s)
    # Do not silently leave the demonstrated simplified joint corridor.
    nearest=np.full(len(s),np.inf)
    for a,b in zip(p[:-1],p[1:]):
        d=b-a;u=np.clip((path-a)@d/(d@d),0,1)
        nearest=np.minimum(nearest,abs(path-(a+u[:,None]*d)).max(axis=1))
    if nearest.max()>32:return smooth_segments(p,velocity,acceleration,dt)
    first=abs(curve(s,1)).max(axis=1);second=abs(curve(s,2)).max(axis=1)
    speed=np.minimum(velocity/np.maximum(first,1e-9),np.sqrt(.45*acceleration/np.maximum(second,1e-9)))
    tangent=.45*acceleration/np.maximum(first,1e-9)
    speed[0]=speed[-1]=0
    for i in range(1,len(s)):
        speed[i]=min(speed[i],np.sqrt(speed[i-1]**2+2*min(tangent[i-1:i+1])*(s[i]-s[i-1])))
    for i in range(len(s)-2,-1,-1):
        speed[i]=min(speed[i],np.sqrt(speed[i+1]**2+2*min(tangent[i:i+2])*(s[i+1]-s[i])))
    time=np.r_[0,np.cumsum(2*np.diff(s)/np.maximum(speed[:-1]+speed[1:],1e-9))]
    tt=np.linspace(0,time[-1],int(np.ceil(time[-1]/dt))+1)
    qq=curve(PchipInterpolator(time,s)(tt))
    vv=np.diff(qq,axis=0)/np.diff(tt)[:,None]
    aa=np.diff(vv,axis=0)/((np.diff(tt)[1:]+np.diff(tt)[:-1])/2)[:,None]
    scale=max(1.,abs(vv).max()/velocity,np.sqrt(abs(aa).max()/acceleration))*1.02
    return tt*scale,qq


def build_routes(times,positions,annotations,velocity=600.,acceleration=1200.,blend=False):
    t=np.asarray(times);q=np.asarray(positions);opened=annotations['open_count']
    state=np.array([np.interp(annotations['cycles'][0]['start'],t,q[:,j]) for j in range(6)])
    stages=[];clock=0.
    def add(cycle,name,points,source_range=None):
        nonlocal state,clock
        generator=blended_segments if blend else smooth_segments
        tt,qq=generator(points,velocity,acceleration)
        stages.append(dict(cycle=cycle,phase=name,start_seconds=clock,duration_seconds=float(tt[-1]),
            source_range=source_range,times=(tt+clock).tolist(),positions=qq.tolist()))
        state=qq[-1].copy();clock+=float(tt[-1])
    for i,c in enumerate(annotations['cycles']):
        # Opening happens at rest BEFORE any approach. Previous release may already open it.
        goal=state.copy();goal[5]=opened
        add(i,'OPEN_BEFORE_APPROACH',np.stack([state,goal]))
        a=annotations['cycles'][i-1]['release_start'] if i else c['start']
        for name,beg,end,grip in [('APPROACH_OPEN',a,c['close_start'],opened),
                                  ('CARRY_CLOSED',c['close_end'],c['release_start'],None)]:
            if name=='CARRY_CLOSED':
                held=(t>=c['close_end'])&(t<c['release_start'])
                grip=float(np.median(q[held,5]))
                goal=state.copy();goal[5]=grip
                add(i,'GRASP_AT_REST',np.stack([state,goal]))
            keep=(t>=beg)&(t<=end)
            for lo,hi in annotations.get('exclude_intervals',[]):
                keep &= ~((t>=lo)&(t<=hi))
            span=q[keep,:5]
            anchor=np.array([np.interp(end,t,q[:,j]) for j in range(5)])
            points=simplify(np.vstack([state[:5],span,anchor]))
            points=np.column_stack([points,np.full(len(points),grip)])
            add(i,name,points,[beg,end])
        goal=state.copy();goal[5]=opened
        add(i,'RELEASE_AT_REST',np.stack([state,goal]))
    return dict(duration_seconds=clock,stages=stages,
        proposal_velocity_counts_s=velocity,proposal_acceleration_counts_s2=acceleration,
        interpolation='PCHIP_CURVATURE_RETIMED' if blend else 'QUINTIC_STOP_AT_EACH_WAYPOINT',
        excluded_source_intervals=annotations.get('exclude_intervals',[]),
        excluded_intervals_bridged_as_unverified_candidates=True,
        joint_corridor_tolerance_counts=32,open_count=opened,
        route_status='OFFLINE_CANDIDATE_REQUIRES_PHYSICAL_REVIEW',autonomous_replay_allowed=False,
        collision_checked=False,cartesian_clearance_verified=False,
        caveat='Joint-space simplification is not Cartesian obstacle avoidance; suspect intervals are not certified repaired')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--episode',type=Path,required=True)
    parser.add_argument('--blend',action='store_true')
    parser.add_argument('--reviewed',action='store_true');args=parser.parse_args()
    p=args.episode
    rows=[json.loads(l) for l in (p/'episode/samples.jsonl').read_text().splitlines()]
    t=np.array([r['elapsed_seconds'] for r in rows])
    q=np.array([[v['position'] for v in sorted(r['motor_readings'],key=lambda v:v['id'])] for r in rows])
    annotation=json.loads((p/'training_annotations.json').read_text())
    if args.reviewed:
        review=json.loads((p/'corrected_training/data_review.json').read_text())
        annotation['exclude_intervals']=review['excluded_suspect_intervals']
    folder='corrected_route_candidates' if args.reviewed else ('blended_route_candidates' if args.blend else 'route_candidates')
    out=p/folder;out.mkdir(exist_ok=False)
    results=[]
    for speed in [300,600,900]:
        candidate=build_routes(t,q,annotation,speed,speed*2,args.blend)
        candidate['raw_recording_seconds']=float(t[-1])
        candidate['reviewed_task_seconds']=annotation['cycles'][-1]['end']-annotation['cycles'][0]['start']
        (out/f'candidate_{speed}.json').write_text(json.dumps(candidate,indent=2))
        results.append({k:v for k,v in candidate.items() if k!='stages'})
    (out/'summary.json').write_text(json.dumps(results,indent=2))
    print(json.dumps(results),flush=True)


if __name__=='__main__':main()
