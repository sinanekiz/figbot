"""Actual CAD cross-sections and release record for DEC-071; no physical claim."""
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from cad.prototype_arm import build_motor_bearing_pb02 as pb
from cad.prototype_arm import build_forma_v6 as v6


def profile(ax, shape, color, old=False):
    section=pb.pb.mesh(shape).section(plane_origin=[0,0,0],plane_normal=[0,1,0])
    for line in section.discrete:
        points=line[:,[0,2]]
        if old:
            ax.plot(points[:,0],points[:,1],color=color,ls='--',lw=1.5,zorder=4)
        else:
            ax.add_patch(Polygon(points,closed=True,facecolor=color,edgecolor=color,lw=1,zorder=2))


def main():
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12})
    fig,axes=plt.subplots(1,2,figsize=(13,6))
    fig.patch.set_facecolor('#fafaf7')
    cases=[
        (axes[0],pb.rotor(),pb.cap_half(1),pb.at_bearing(pb.pb.cap(pb.SPEC)),
         (49,66),(66,73),68.5,69.5,'PB02 — mevcut taban için','0,4 → 1,0 mm'),
        (axes[1],v6.rotor(),v6.retainer_half(1),v6.ring(53,70,60.5,3.5),
         (51,66),(58,65.5),60,61.4,'FORMA V6 — yeni tasarım','0,5 → 1,4 mm (düz tabla)')]
    for ax,rotor,cap,old,xlim,ylim,top,roof,title,gaptext in cases:
        ax.set_facecolor('#fafaf7')
        profile(ax,rotor,'#d28a35');profile(ax,cap,'#237b7e');profile(ax,old,'#7c8790',True)
        x=53.6
        ax.annotate('',xy=(x,roof),xytext=(x,top),arrowprops={'arrowstyle':'<->','color':'#b22537','lw':2},zorder=6)
        ax.text(54.3,(top+roof)/2,gaptext,color='#b22537',va='center',fontsize=12,
                bbox={'facecolor':'white','alpha':.96,'edgecolor':'none'},zorder=7)
        ax.set(xlim=xlim,ylim=ylim,title=title,xlabel='Merkezden uzaklık (mm)',ylabel='Yükseklik (mm)')
        ax.set_aspect('equal');ax.grid(alpha=.15)
        ax.spines[['top','right']].set_visible(False)
    fig.suptitle('İç üst dudakta açılan boşluk',fontsize=23,fontweight='bold',y=.97)
    fig.text(.5,.13,'Turkuaz: yeni sabit çerçeve   •   Turuncu: dönen tabla   •   Kesikli: eski iç yüzey',ha='center',fontsize=12)
    fig.text(.5,.08,'V6 taşıyıcı köşeleri bu kesit dışında: önce 0,1 mm, şimdi en az 1,0 mm boşluk.',ha='center',fontsize=11)
    fig.text(.5,.035,'Gerçek CAD kesiti. Baskı sonrası sürtünme, eğilme ve tutunma fiziksel olarak doğrulanmalı.',ha='center',fontsize=10,color='#57616a')
    fig.subplots_adjust(top=.85,bottom=.23,wspace=.25,left=.065,right=.985)
    target=pb.ROOT/'reports/20260912_RULMAN_KAPAK_BOSLUGU.png'
    fig.savefig(target,dpi=160)
    report={'decision':'DEC-071','physical_validation':False,'motor_commands_sent':False,
      'PB02':{'original_axial_gap_mm':.4,'new_axial_gap_mm':1.,'roof_thickness_mm':2.4,
              'replacement_parts':['PB02_03A_YAN_KAPAK','PB02_03B_YAN_KAPAK'],'output':str(pb.OUT)},
      'FORMA_V6':{'original_flange_gap_mm':.5,'original_corner_gap_mm':.1,
                  'new_flange_gap_mm':1.4,'new_corner_gap_mm':1.,'roof_thickness_mm':2.6,
                  'replacement_parts':['F6-03A-RETAINER','F6-03B-RETAINER'],'relief_outer_radius_mm':60},
      'unchanged':['motor locations','rotors','ball grooves','balls','fastener positions','bearing axes'],
      'limits':'This axial relief does not correct motor eccentricity or establish strength/tilt/friction.'}
    (pb.ROOT/'reports/20260912_RULMAN_KAPAK_BOSLUGU.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(target,flush=True)


if __name__=='__main__':main()
