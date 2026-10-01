"""Bounded exploratory jaw closure; contact indication is NOT grasp proof."""
import time
from .protocol import BusError


def close_jaw(control, floor, camera_fresh, stopped=lambda: False,
              record=lambda e: None, clock=time.monotonic, sleep=time.sleep):
    if control.state != 'HOLDING' or not camera_fresh() or stopped():
        raise BusError('Stationary hold and fresh camera required')
    initial = control.read_all(); control.validate_rows(initial)
    if any(r['torque'] != 1 or r['speed'] or r['moving'] for r in initial.values()):
        raise BusError('Stationary enabled chain required')
    start = initial[6]['position']
    if type(floor) is not int or floor not in (935,975,1010) or not floor < start <= 1580:
        raise BusError('Only explicitly reviewed demonstration jaw floors are supported')
    baseline = abs(initial[6]['current_raw'])
    if baseline >= 8:
        raise BusError('Jaw current elevated before closure')
    deadline = clock() + 40
    control.state = 'GRASPING'; control.active = None
    reason = 'DEMONSTRATED_CLOSURE_REACHED'
    try:
        actual = start
        # Allow measured servo deadband without increasing the positional floor.
        for attempt in range((start-floor+11)//12+2):
            if stopped() or not camera_fresh() or clock() > deadline:
                raise BusError('Closure STOP/camera/deadline')
            target = max(floor, actual - 24)
            control.goal_verified(6, target, speed=60, acceleration=1)
            control.targets[6] = target
            began = clock(); stable = None; previous = None; contact = False
            while clock() - began < 1.7:
                if stopped() or not camera_fresh() or clock() > deadline:
                    raise BusError('Closure STOP/camera/deadline')
                rows = control.read_all(); control.validate_rows(rows)
                if any(r['torque'] != 1 for r in rows.values()):
                    raise BusError('Torque lost')
                if any(abs(rows[i]['position']-initial[i]['position']) > 12 or
                       abs(rows[i]['speed']) > 50 for i in range(1, 6)):
                    raise BusError('Arm moved during jaw closure')
                r = rows[6]; actual = r['position']
                if not floor-8 <= actual <= start+8:
                    raise BusError('Jaw excursion exceeded')
                record(dict(attempt=attempt, target=target, rows=rows, time=clock()))
                # Conservative raw-current stop only, not calibrated force sensing.
                if abs(r['current_raw']) >= min(8, baseline+5):
                    reason = 'CURRENT_RISE_CONTACT_CANDIDATE'; contact = True; break
                stationary = not r['moving'] and abs(r['speed']) <= 5
                if stationary and previous is not None and abs(actual-previous) <= 2:
                    if stable is None: stable = clock()
                else: stable = None
                previous = actual
                if stable is not None and clock()-stable >= .16:
                    if actual-target >= 12:
                        reason = 'RESIDUAL_CONTACT_CANDIDATE'; contact = True
                    break
                sleep(.04)
            else:
                raise BusError('Jaw failed to settle')
            if contact or actual <= floor+8: break
        else: raise BusError('Closure step budget exhausted')
        # Remove any residual squeeze command at first resistance.
        if not control.pause('Jaw closure complete; measured hold'):
            raise BusError('Jaw hold failed')
        until = clock()+.6
        while clock() < until:
            if stopped() or not camera_fresh(): raise BusError('Closure final hold gate')
            control.poll(camera_fresh())
            if control.state != 'PAUSED_HOLD': raise BusError('Closure final hold fault')
            sleep(.04)
        control.resume_existing_hold(camera_fresh())
        return dict(state='CLOSED_HOLDING_UNVERIFIED_GRASP', reason=reason,
                    jaw=control.rows[6]['position'], rows=control.rows)
    except Exception as e:
        control.pause('Closure stopped: '+str(e), fault=True)
        raise
