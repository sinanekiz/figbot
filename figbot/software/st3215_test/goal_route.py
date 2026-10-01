"""Generate joint-space travel from task targets, never a taught intermediate path.

The small shoulder bow is a geometric clearance aid, not collision detection.
No bus access, torque enabling, coordinate wrapping, or calibration changes.
"""
import math
from .protocol import BusError


def build_goal_route(start,home,pickup,basket,*,cycles=2,speed_limit=1200,
                     acceleration=50,clearance_counts=64,release_lead=.18,opening_seconds=.56,
                     home_joint_speed_limit=1000):
    for pose in (start,home,pickup,basket):
        if set(pose)!=set(range(1,7)) or any(type(p)!=int or not 0<=p<=4095 for p in pose.values()):
            raise BusError('Hedefler altı geçerli ham motor konumu içermeli.')
    if type(cycles)!=int or not 1<=cycles<=3:raise BusError('1–3 doğrudan çevrim gerekli.')
    if type(speed_limit)!=int or not 1<=speed_limit<=3400:raise BusError('Hedef sürüş hızı geçersiz.')
    if type(home_joint_speed_limit)!=int or not 1<=home_joint_speed_limit<=3400:raise BusError('Başlangıç omuz/dirsek hız sınırı geçersiz.')
    if type(acceleration)!=int or not 1<=acceleration<=150:raise BusError('Hedef sürüş ivmesi geçersiz.')
    if type(clearance_counts)!=int or not 0<=clearance_counts<=64:raise BusError('Omuz açıklık yayı 0–64 sayım olmalı.')
    if any(type(v) not in (int,float) or not math.isfinite(v) for v in (release_lead,opening_seconds)) or not 0<=release_lead<=.25 or not release_lead<opening_seconds<=2:
        raise BusError('Hedef bırakma zamanlaması geçersiz.')
    if basket[6]<=pickup[6]:raise BusError('Bırakma açıklığı kavrama konumundan büyük olmalı.')
    start=dict(start);home=dict(home);pickup=dict(pickup);basket=dict(basket)
    for pose in (home,pickup,basket):pose[5]=start[5]
    closed=pickup[6];opened=basket[6];current=dict(start);waypoints=[]
    metadata=dict(goal_only=True,harvest_windows=[],generated_legs=[],speed_limit=speed_limit,
                  acceleration_limit=acceleration,clearance_counts=clearance_counts,
                  home_joint_speed_limit=home_joint_speed_limit)

    def leg(target,*,bow=False,mid_jaw=None,home_leg=False):
        nonlocal current
        target=dict(target);target[5]=start[5]
        delta=max(abs(target[i]-current[i]) for i in (1,2,3,4))
        if not delta:raise BusError('Doğrudan hedefte kol hareketi yok.')
        if delta>=2048:raise BusError('Hedef enkoder dalı belirsiz; otomatik sarma yok.')
        seconds=max(.3,1.875*delta/speed_limit,math.sqrt(5.773503*delta/(acceleration*100)))
        if home_leg:
            # Unfold/fold loads the shoulder and elbow differently from the
            # harvesting transfer. Cap those axes without changing loop timing.
            seconds=max(seconds,*(1.875*abs(target[i]-current[i])/home_joint_speed_limit for i in (2,3)))
        middle={i:round((current[i]+target[i])/2) for i in range(1,7)}
        if bow:
            # Stay within the two target shoulder positions; no new joint range.
            middle[2]=max(min(current[2],target[2]),middle[2]-clearance_counts)
        if mid_jaw is not None:middle[6]=mid_jaw
        for pose,extra in ((middle,dict(goal_midpoint=True)),(target,dict(goal_stop=True))):
            if any(abs(pose[i]-current[i])>1024 for i in pose):
                raise BusError('Hesaplanan hedef aralığı 90 dereceyi aşıyor.')
            waypoints.append(dict(positions={str(i):v for i,v in pose.items()},seconds=.25,stream_seconds=seconds/2,**extra))
            current=dict(pose)
        metadata['generated_legs'].append(dict(end_knot=len(waypoints),seconds=seconds,
                                               shoulder_bow=bool(bow),home_leg=bool(home_leg)))

    def carry_and_release():
        nonlocal current
        target={**basket,6:closed}
        leg(target,bow=True,mid_jaw=closed)
        waypoints[-1]['release_gate']=True
        if release_lead:waypoints[-1]['release_lead_seconds']=release_lead
        waypoints.append(dict(positions={str(i):v for i,v in basket.items()},seconds=.25,
                              stream_seconds=opening_seconds-release_lead,goal_stop=True))
        current=dict(basket)

    leg(pickup,mid_jaw=opened,home_leg=True)
    carry_and_release()
    for _ in range(cycles):
        start_knot=len(waypoints)
        leg(pickup,bow=True,mid_jaw=opened)
        carry_and_release()
        metadata['harvest_windows'].append(dict(start_knot=start_knot,end_knot=len(waypoints)))
    leg(home,mid_jaw=closed,home_leg=True)
    return waypoints,metadata
