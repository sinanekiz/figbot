"""Continuous, shape-preserving joint paths; no hardware access.

Every knot is passed at its scheduled time, without an arrival/stop handshake.
PCHIP has continuous velocity (C1); optional quintic C2 also has continuous
acceleration. Both validate exact polynomial position, speed and acceleration
extrema. Neither promises continuous jerk or measured mechanical smoothness.
This is not Cartesian collision planning or force-controlled grasping.
"""
import numpy as np
from scipy.interpolate import PchipInterpolator, CubicHermiteSpline, BPoly, PPoly
from .protocol import BusError
from .coordinated import MAX_SPEED


def polynomial_extrema(coefficients, duration, derivative=0):
    coefficients=np.polyder(coefficients,derivative)
    roots=np.roots(np.polyder(coefficients)) if len(coefficients)>1 else []
    times=[0.,duration]+[float(z.real) for z in roots if abs(z.imag)<1e-8 and 0<z.real<duration]
    return np.asarray([np.polyval(coefficients,t) for t in times])


class SmoothPath:
    def __init__(self, start, plan, acceleration, *, curve_kind='pchip'):
        if curve_kind not in ('pchip','quintic_c2'):raise BusError('Bilinmeyen sürekli yörünge türü.')
        if any(w['dwell'] for w in plan):
            raise BusError('Sürekli yörünge bekleme duruşu içeremez.')
        points=[list(start.values())];times=[0.];release_knots=[];goal_midpoints=[];goal_stops=[]
        for w in plan:
            point=[w['positions'][i] for i in start]
            if point==points[-1]:
                if w.get('release_gate') or w.get('goal_midpoint') or w.get('goal_stop'):raise BusError('Hedef düğümü yinelenemez.')
                continue
            points.append(point);times.append(times[-1]+w.get('stream_seconds',w['seconds']))
            if w.get('release_gate'):release_knots.append((len(points)-1,w.get('release_lead_seconds',0.)))
            if w.get('goal_midpoint'):goal_midpoints.append(len(points)-1)
            if w.get('goal_stop'):goal_stops.append(len(points)-1)
        if len(points)<2:raise BusError('Sürekli yörüngede hareket yok.')
        self.ids=list(start);y=np.asarray(points,dtype=float);t=np.asarray(times)
        jaw_times=t.copy()
        for k,lead in release_knots:
            if (6 not in self.ids or k+1>=len(points) or
                    any(points[k][j]!=points[k+1][j] for j,i in enumerate(self.ids) if i!=6) or
                    points[k+1][self.ids.index(6)]<=points[k][self.ids.index(6)]):
                raise BusError('Bırakma için aynı kol duruşunda kapalı ve açık kıskaç gerekli.')
            if lead and (curve_kind!='quintic_c2' or not 0<lead<=.25 or lead>=t[k]-t[k-1]):
                raise BusError('Yaklaşmada açılma payı önceki C2 taşıma aralığına sığmalı.')
            jaw_times[k]-=lead
        def build(scale):
            curves=[]
            for j,i in enumerate(self.ids):
                knots=(jaw_times if i==6 else t)*scale
                v=PchipInterpolator(knots,y[:,j]).derivative()(knots);v[0]=0;v[-1]=0
                if i!=6:
                    for k in goal_stops:v[k]=0.
                    for k in goal_midpoints:
                        if (k+1>=len(points) or not np.isclose(t[k]-t[k-1],t[k+1]-t[k],rtol=1e-7,atol=1e-8)):
                            raise BusError('Doğrudan geçiş düğümü zaman aralığının ortasında olmalı.')
                        # Midpoint derivative of a single minimum-jerk target
                        # move. Splitting validates<=1024 counts without adding
                        # an artificial slowdown or stop halfway to the goal.
                        v[k]=1.875*(y[k+1,j]-y[k-1,j])/(knots[k+1]-knots[k-1])
                if i==6:
                    for k,lead in release_knots:
                        if lead:v[k]=0;v[k+1]=0
                if curve_kind=='quintic_c2':
                    curves.append(PPoly.from_bernstein_basis(BPoly.from_derivatives(knots,[[p,z,0.] for p,z in zip(y[:,j],v)])))
                else:curves.append(CubicHermiteSpline(knots,y[:,j],v))
            return curves
        curves=build(1.)
        # Exact extrema for either cubic or quintic polynomial segments.
        vmax=0.;amax=0.
        for k,curve in enumerate(curves):
            for j,h in enumerate(np.diff(curve.x)):
                coeff=curve.c[:,j]
                extrema=polynomial_extrema(coeff,h)
                if extrema.min()<min(y[j,k],y[j+1,k])-1e-5 or extrema.max()>max(y[j,k],y[j+1,k])+1e-5:
                    raise BusError('Sürekli eğri kayıtlı iki duruşun dışına taşıyor.')
                vmax=max(vmax,float(np.max(np.abs(polynomial_extrema(coeff,h,1)))))
                amax=max(amax,float(np.max(np.abs(polynomial_extrema(coeff,h,2)))))
        scale=max(1.,vmax/MAX_SPEED,(amax/(acceleration*100))**.5)
        self.times=t*scale;self.duration=float(self.times[-1])
        if self.duration>50:raise BusError('Sürekli yörünge zaman bütçesini aşıyor.')
        curves=build(scale)
        self.curve=lambda seconds,nu=0:np.stack([c(seconds,nu) for c in curves],axis=-1)
        self.curve_kind=curve_kind
        self.bounds={i:(int(y[:,k].min()),int(y[:,k].max())) for k,i in enumerate(self.ids)}
        self.moving=[i for i,(lo,hi) in self.bounds.items() if lo!=hi]
        self.final={i:int(y[-1,k]) for k,i in enumerate(self.ids)}
        self.max_speed=vmax/scale;self.max_acceleration=amax/scale**2
        self.checkpoints=[];self.release_windows=[]
        for k,lead in release_knots:
            pose={i:int(points[k][j]) for j,i in enumerate(self.ids) if i!=6}
            opening=float(self.times[k]-lead*scale)
            checkpoint=dict(seconds=opening,positions=pose,phase='basket_arrival')
            if lead:
                index=len(self.release_windows)
                self.release_windows.append(dict(index=index,start=opening,arrival=float(self.times[k]),end=float(self.times[k+1]),
                    duration=float(self.times[k+1]-opening),closed=int(points[k][self.ids.index(6)]),opened=int(points[k+1][self.ids.index(6)]),position=pose))
                checkpoint.update(phase='approach_release',window=index)
            self.checkpoints.extend([checkpoint,dict(seconds=float(self.times[k+1]),positions={i:int(points[k+1][j]) for j,i in enumerate(self.ids)},phase='release_complete')])

    def sample(self, seconds):
        values=self.curve(min(self.duration,max(0.,seconds)))
        return {i:int(round(v)) for i,v in zip(self.ids,values)}

    def runtime_sample(self, phase, wall_elapsed, release_started, anticipation=0., phase_cap=None):
        result=self.sample(min(phase+anticipation,phase_cap) if phase_cap is not None else phase+anticipation)
        for w in self.release_windows:
            if phase>w['end']+1e-8:continue
            if phase<w['start']:
                if phase+anticipation>=w['start']:result[6]=w['closed']
                break
            start=release_started.get(w['index'])
            u=0. if start is None else min(1.,max(0.,(wall_elapsed-start+anticipation)/w['duration']))
            blend=10*u**3-15*u**4+6*u**5
            result[6]=round(w['closed']+(w['opened']-w['closed'])*blend)
            break
        return result


class SmoothMotion:
    def play_smooth(self, waypoints, camera_fresh, *, taught_envelopes=None, curve_kind='pchip'):
        start,plan=self._prepare_plan(waypoints,camera_fresh,taught_envelopes,continuous=True)
        path=SmoothPath(start,plan,self.motion_acceleration_limit,curve_kind=curve_kind)
        self.smooth_path=path
        # Configure finite hardware limits once, then stream Goal_Position only,
        # matching LeRobot's continuous send_action pattern.
        profiles={i:(start[i],MAX_SPEED,self.motion_acceleration_limit) for i in path.moving}
        self.targets=dict(start);self.state='MOVING'
        try:
            self.bus.sync_goal(profiles)
            for i,(p,v,a) in profiles.items():
                if self.bus.read(i,41,7)!=bytes([a])+p.to_bytes(2,'little')+b'\0\0'+v.to_bytes(2,'little'):
                    raise BusError('Sürekli sürüş profili geri okunamadı.')
            now=self.clock()
            self.active=dict(kind='smooth_path',started=now,last_sample=now,
                seconds=path.duration,deadline=now+path.duration+1.5,
                knots=path.times.tolist(),sample_count=0,max_gap=0.,max_tracking_error=0,
                index=0,joints=path.moving,curve_kind=curve_kind,
                time_offset=0.,scheduler_delay=0.,scheduler_delays=0,
                checkpoint_index=0,checkpoint_wait_started=None,checkpoint_events=[],release_started={})
            self.message='Sürekli yörünge başladı; ara noktalarda duruş beklenmiyor.'
        except Exception as exc:
            self.pause(str(exc),fault=True);raise

    def _poll_smooth(self, rows):
        a=self.active;p=self.smooth_path;now=self.clock();wall_elapsed=now-a['started'];elapsed=wall_elapsed-a['time_offset']
        gap=now-a['last_sample']
        if gap>.25:raise BusError('Sürekli sürüş örneklemesi gecikti; yol iptal edildi.')
        if now>a['deadline']:raise BusError('Sürekli sürüş bitişi doğrulanamadı.')
        if gap>.08:
            # A Windows scheduling stall is not executed trajectory time. The
            # servos only received a nearby goal before the stall; advancing by
            # the entire wall gap can jump the reference beyond that goal.
            # Resume with at most two nominal ticks. Keep the original deadline
            # and 192-count tracking/goal guards: repeated stalls still expire.
            delay=gap-.04
            a['time_offset']+=delay;a['scheduler_delay']+=delay;a['scheduler_delays']+=1
            elapsed=wall_elapsed-a['time_offset']
        checkpoint=p.checkpoints[a['checkpoint_index']] if a['checkpoint_index']<len(p.checkpoints) else None
        if checkpoint and elapsed>=checkpoint['seconds']:
            # The supported arm's held encoder jitters by1–2 counts. Keep a
            # 2-count measurement allowance at arrival rather than waiting
            # for a loaded shoulder to cross the20-count edge by one count.
            approach=checkpoint['phase']=='approach_release'
            tolerance=22 if checkpoint['phase']=='basket_arrival' else 20
            if approach:
                ready=all(abs(rows[i]['position']-pos)<=(22 if i==5 else 64) and
                    (abs(pos-rows[i]['position'])<=22 or rows[i]['speed']*np.sign(pos-rows[i]['position'])>=-50)
                    for i,pos in checkpoint['positions'].items())
            else:
                ready=all(abs(rows[i]['position']-pos)<=(22 if i!=6 else tolerance) and
                          (checkpoint['phase']!='basket_arrival' or abs(rows[i]['speed'])<=100)
                          for i,pos in checkpoint['positions'].items())
            if ready:
                if approach:a['release_started'][checkpoint['window']]=wall_elapsed
                a['checkpoint_events'].append(dict(phase=checkpoint['phase'],elapsed=now-a['started'],positions={i:r['position'] for i,r in rows.items()}))
                a['checkpoint_index']+=1;a['checkpoint_wait_started']=None
                checkpoint=p.checkpoints[a['checkpoint_index']] if a['checkpoint_index']<len(p.checkpoints) else None
            else:
                if a['checkpoint_wait_started'] is None:a['checkpoint_wait_started']=now
                if now-a['checkpoint_wait_started']>.75:
                    raise BusError('Sepet konumu/kıskaç bırakması doğrulanamadı; yol iptal edildi.')
                stop_at=p.release_windows[checkpoint['window']]['arrival'] if approach else checkpoint['seconds']
                if elapsed>stop_at:
                    delay=elapsed-stop_at;a['time_offset']+=delay;a['deadline']+=delay
                    elapsed=stop_at
        expected=p.runtime_sample(elapsed,wall_elapsed,a['release_started'])
        for i,r in rows.items():
            lo,hi=p.bounds[i]
            if r['torque']!=1 or not lo-32<=r['position']<=hi+32:
                raise BusError(f'ID{i}: sürekli sürüş aralığı/tutması kayboldu.')
            error=abs(r['position']-expected[i])
            a['max_tracking_error']=max(a['max_tracking_error'],error)
            if error>(192 if i in p.moving else 32):
                raise BusError(f'ID{i}: sürekli yörünge takibi saptı ({error} sayım).')
        # A short finite lookahead prevents the motor waiting at each sample.
        # If the host stops, hardware has only this nearby goal, not a full run.
        # Reduce anticipation near the relative-target cap rather than removing
        # that cap or aborting a valid, still-tracked path merely for lookahead.
        for lead in (.10,.075,.05,.025,0.):
            cap=(p.release_windows[checkpoint['window']]['arrival'] if checkpoint['phase']=='approach_release' else checkpoint['seconds']) if checkpoint else p.duration
            goal=p.runtime_sample(elapsed,wall_elapsed,a['release_started'],lead,cap)
            if all(abs(goal[i]-rows[i]['position'])<=192 for i in p.moving):break
        changes={i:goal[i] for i in p.moving if goal[i]!=self.targets[i]}
        if any(abs(v-rows[i]['position'])>192 for i,v in changes.items()):
            raise BusError('Sürekli hedef mevcut konumdan fazla uzaklaştı.')
        if changes:
            self.bus.sync_positions(changes)
            for i,v in changes.items():
                if int.from_bytes(self.bus.read(i,42,2),'little')!=v:
                    raise BusError('Sürekli hedef geri okuması uyuşmuyor.')
            self.targets.update(changes)
        a['sample_count']+=1;a['max_gap']=max(a['max_gap'],gap);a['last_sample']=now
        a['index']=int(np.searchsorted(p.times,elapsed,side='right'))
        if elapsed>=p.duration and all(abs(r['position']-p.final[i])<=20 and
                abs(r['speed'])<=50 and not r['moving'] for i,r in rows.items()):
            self.last_smooth_result={**a,'elapsed':now-a['started'],'trajectory_elapsed':elapsed,
                'final_positions':{i:r['position'] for i,r in rows.items()}}
            self.active=None;self.state='HOLDING'
            self.message='Sürekli çevrim tamamlandı; kapalı başlangıç korunuyor.'
