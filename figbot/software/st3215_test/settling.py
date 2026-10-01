"""Explicit, bounded correction of a stationary joint residual. No EEPROM writes.

Opt-in supervised operation: nominal target plus at most three 12-count SRAM
goal trims. Checks measured position, preserves all other held joints and ends
in a freshly measured hold. This is not a force controller or a fault bypass.
"""
import time
from .protocol import BusError


def settle_joint(control, joint, desired, envelope, camera_fresh, stopped=lambda:False,
                 record=lambda event:None, clock=time.monotonic, sleep=time.sleep):
    if joint != 2 or type(desired) is not int:
        raise BusError('This reviewed correction is limited to shoulder ID2')
    if control.state != 'HOLDING' or not camera_fresh() or stopped():
        raise BusError('Verified stationary hold and fresh camera required')
    initial=control.read_all();control.validate_rows(initial)
    if any(r['torque']!=1 or r['speed']!=0 or r['moving'] for r in initial.values()):
        raise BusError('Every joint must already be holding stationary')
    start=initial[joint]['position']
    if abs(start-desired)>64 or not envelope[0]<=desired<=envelope[1]:
        raise BusError('Correction must remain near the measured target')
    target=desired;events=[];deadline=clock()+8;converged=False
    control.active=None;control.state='SETTLING'
    try:
        for attempt in range(4):
            if not camera_fresh() or stopped():raise BusError('Camera/STOP gate')
            if abs(target-desired)>36 or not envelope[0]<=target<=envelope[1]:
                raise BusError('Bounded correction range exhausted')
            control.goal_verified(joint,target,speed=60,acceleration=1)
            control.targets[joint]=target
            began=clock();stable_since=None;previous=None
            while clock()-began<1.7:
                if clock()>deadline or not camera_fresh() or stopped():
                    raise BusError('Correction deadline/camera/STOP gate')
                rows=control.read_all();control.validate_rows(rows)
                if any(r['torque']!=1 for r in rows.values()):raise BusError('Torque lost')
                if any(abs(r['position']-initial[i]['position'])>12 or abs(r['speed'])>50
                       for i,r in rows.items() if i!=joint):
                    raise BusError('Another held joint moved during correction')
                actual=rows[joint]['position']
                if not min(start,desired)-48<=actual<=max(start,desired)+48:
                    raise BusError('Correction excursion exceeded')
                event=dict(attempt=attempt,desired=desired,command=target,actual=actual,
                           speed=rows[joint]['speed'],time=clock(),rows=rows)
                record(event)
                stationary=not rows[joint]['moving'] and abs(rows[joint]['speed'])<=5
                if stationary and previous is not None and abs(actual-previous)<=2:
                    if stable_since is None:stable_since=clock()
                else:stable_since=None
                previous=actual
                if stable_since is not None and clock()-stable_since>=.3:
                    events.append({k:event[k] for k in ['attempt','desired','command','actual']})
                    error=desired-actual
                    if abs(error)<=8:converged=True
                    else:target+=max(-12,min(12,error))
                    break
                sleep(.04)
            else:raise BusError('Joint failed to settle within bounded correction')
            if converged:break
        if not converged:raise BusError('Bounded correction did not converge')
        if not control.pause('Corrected endpoint; establish measured hold'):
            raise BusError('Measured hold write failed')
        until=clock()+.55
        while clock()<until:
            if not camera_fresh() or stopped():raise BusError('Camera/STOP during final hold')
            rows=control.poll(camera_fresh())
            if control.state!='PAUSED_HOLD':raise BusError('Final hold fault')
            sleep(.04)
        if abs(rows[joint]['position']-desired)>20:
            raise BusError('Endpoint moved outside original arrival tolerance')
        control.resume_existing_hold(camera_fresh())
        return dict(state='CORRECTED_HOLDING',desired=desired,actual=rows[joint]['position'],
                    attempts=events,limits_unchanged=True,eeprom_writes=False)
    except Exception as error:
        control.pause('Bounded correction stopped: '+str(error),fault=True)
        raise
