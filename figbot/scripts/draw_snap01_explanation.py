"""Schematic only: illustrates intended stack, not measured fit or revised CAD."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch, FancyArrowPatch

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'cad/prototype_arm/snap01'

def main():
    plt.rcParams['font.family']='DejaVu Sans'
    fig=plt.figure(figsize=(14,11),facecolor='#f5f7fa')
    ax=fig.add_axes([0,0,1,1]);ax.set_xlim(0,1400);ax.set_ylim(0,1100);ax.axis('off')
    blue='#168cb2';orange='#ef9a32';grey='#6c7789';black='#242d38';gold='#c69932';ink='#182d42'
    def txt(x,y,s,size=14,c=ink,**kw):ax.text(x,y,s,fontsize=size,color=c,va='top',**kw)
    def rect(x,y,w,h,c):ax.add_patch(Rectangle((x,y),w,h,facecolor=c,edgecolor='none'))
    def arrow(start,end,c=ink):ax.add_patch(FancyArrowPatch(start,end,arrowstyle='-|>',mutation_scale=15,color=c,linewidth=1.6))
    def number(x,y,n,c):ax.add_patch(Circle((x,y),19,color=c));ax.text(x,y,str(n),color='white',ha='center',va='center',fontsize=16,weight='bold')
    txt(55,1060,'Neyin nereye oturması planlandı?',25,weight='bold')
    txt(55,1015,'Şematik yan kesit • Ölçekli değildir • Mevcut baskının uyduğunu göstermez',12,c='#586a7a')
    ax.add_patch(FancyBboxPatch((40,265),1320,705,boxstyle='round,pad=0,rounding_size=18',facecolor='white',edgecolor='#dde4ec'))

    # Motor outside enclosure. Output shaft points down into original horn.
    rect(548,742,240,158,black)
    rect(515,754,306,22,black)
    rect(600,703,136,39,black)
    rect(656,626,24,77,gold)
    txt(668,848,'MG996R',18,c='white',ha='center',weight='bold')
    txt(668,815,'MOTOR',15,c='white',ha='center')

    # Printed cup, front screw access through its floor.
    rect(480,410,170,34,blue);rect(686,410,170,34,blue)
    rect(480,444,35,140,blue);rect(821,444,35,140,blue)
    # Front/rear rail shoulders shown in cross section.
    rect(480,568,70,16,blue);rect(786,568,70,16,blue)
    # Original horn plate and hub, sectioned so centre bore is visible.
    rect(532,457,124,35,grey);rect(680,457,124,35,grey)
    rect(624,492,32,158,grey);rect(680,492,32,158,grey)
    # Sliding cap's large centre aperture clears the hub conceptually.
    rect(518,535,91,23,orange);rect(727,535,91,23,orange)
    ax.plot([668,668],[365,729],linestyle=(0,(5,5)),color='#8192a3',linewidth=1)

    number(95,855,4,black)
    txt(126,869,'Motor DIŞARIDA kalır',19,weight='bold')
    txt(126,831,'Motor gövdesi mavi kutunun\niçine girmeyecek.',14)
    arrow((428,821),(540,804))

    number(95,625,3,orange)
    txt(126,640,'Turuncu: kayar kapak',18,weight='bold')
    txt(126,603,'Yandan raylara girer.\nPlastik başlığın geniş kısmını\niçeride tutmayı amaçlar.',14)
    arrow((430,588),(542,548),orange)
    arrow((408,533),(487,533),orange)
    txt(393,511,'kaydır',11,c='#ab610c')

    number(95,438,1,blue)
    txt(126,452,'Mavi: baskı gövde',18,weight='bold')
    txt(126,415,'İçindeki cebe motorun\nplastik başlığı yerleşir.',14)
    arrow((419,412),(487,430),blue)

    txt(932,853,'Altın renk: motor mili',17,c='#986d17',weight='bold')
    txt(932,815,'Plastik başlığın ortasındaki\ndişli deliğe girer.',14)
    arrow((954,771),(670,680),gold)

    number(917,684,2,grey)
    txt(947,700,'Gri: plastik başlık',18,weight='bold')
    txt(947,662,'Motor kutusundan çıkan\nyıldız veya disk parça.\nBurada KESİT olarak çizildi.',14)
    arrow((947,591),(703,607),grey)

    txt(934,516,'Kapaktaki BÜYÜK delik',16,c='#aa650d',weight='bold')
    txt(934,481,'Başlığın orta çıkıntısı\nburadan geçer.\nMotorun gövdesi geçmez.',14)
    arrow((928,445),(731,541),orange)

    arrow((668,332),(668,433),blue)
    txt(668,324,'Alttaki KÜÇÜK delik: merkez vidasına erişim',14,ha='center',weight='bold')
    txt(668,294,'Merkez vidası başlığı motor milinde tutar; bu çizimde vida gösterilmedi.',11,ha='center')

    ax.add_patch(FancyBboxPatch((40,45),1320,193,boxstyle='round,pad=0,rounding_size=16',facecolor='#fff1df',edgecolor='#f0c28f'))
    txt(65,217,'Sende neden kapanmıyor olabilir?',18,c='#8b430d',weight='bold')
    txt(65,178,'• Başlığın orta çıkıntısı turuncu deliğe sığmıyor olabilir.\n• Başlığın kalınlığı, kapak altındaki boşluktan büyük olabilir.\n• Kapak kapansa bile motor kasasına dayanıp milin tam oturmasını engelleyebilir.',14,c='#633f24')
    txt(65,84,'Zorlama veya delme. Bu temas yerini fotoğrafta görüp geometriyi düzeltmemiz gerekiyor.',14,c='#8b430d',weight='bold')
    OUT.mkdir(parents=True,exist_ok=True)
    fig.savefig(OUT/'NEY_NEREYE_OTURACAK.png',dpi=150,facecolor=fig.get_facecolor())
    fig.savefig(OUT/'NEY_NEREYE_OTURACAK.svg',facecolor=fig.get_facecolor())
    plt.close(fig)
    print(OUT/'NEY_NEREYE_OTURACAK.png')

if __name__=='__main__':main()
