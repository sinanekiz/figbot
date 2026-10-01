import numpy as np
from cad.prototype_arm.export_forma_v6 import mesh

def render(items,path,title,az=-58,el=24,revision=None):
    # CAD z-buffer renderer; do not use generated artwork as dimensional evidence.
    from PIL import Image,ImageDraw,ImageFont
    w,h=1600,1100;meshes=[(mesh(i.shape),i.color) for i in items]
    az,el=np.radians([az,el]);basis=np.array([[-np.sin(az),-np.sin(el)*np.cos(az),np.cos(el)*np.cos(az)],
        [np.cos(az),-np.sin(el)*np.sin(az),np.cos(el)*np.sin(az)],[0,np.cos(el),np.sin(el)]])
    points=np.vstack([m.vertices@basis for m,c in meshes]);center=(points.min(0)+points.max(0))/2
    scale=min((w-140)/np.ptp(points[:,0]),(h-200)/np.ptp(points[:,1]))
    pixels=np.full((h,w,3),(244,243,239),dtype=np.uint8);depth=np.full((h,w),-np.inf)
    light=np.array([-.4,-.5,1]);light/=np.linalg.norm(light)
    for m,color in meshes:
        shades=.62+.37*np.abs(m.face_normals@light);coords=m.vertices@basis
        coords[:,0]=(coords[:,0]-center[0])*scale+w/2
        coords[:,1]=h/2-(coords[:,1]-center[1])*scale
        for k,face in enumerate(m.faces):
            t=coords[face];aa,b,c=t
            x0=max(0,int(np.floor(t[:,0].min())));x1=min(w-1,int(np.ceil(t[:,0].max())))
            y0=max(0,int(np.floor(t[:,1].min())));y1=min(h-1,int(np.ceil(t[:,1].max())))
            det=(b[1]-c[1])*(aa[0]-c[0])+(c[0]-b[0])*(aa[1]-c[1])
            if abs(det)<1e-9 or x1<x0 or y1<y0:continue
            yy,xx=np.mgrid[y0:y1+1,x0:x1+1];xx=xx+.5;yy=yy+.5
            u=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/det
            v=((c[1]-aa[1])*(xx-c[0])+(aa[0]-c[0])*(yy-c[1]))/det
            q=1-u-v;z=u*aa[2]+v*b[2]+q*c[2];target=depth[y0:y1+1,x0:x1+1]
            mask=(u>=-1e-7)&(v>=-1e-7)&(q>=-1e-7)&(z>target)
            target[mask]=z[mask];pixels[y0:y1+1,x0:x1+1][mask]=np.clip(np.array(color)*shades[k]*255,0,255)
    im=Image.fromarray(pixels);d=ImageDraw.Draw(im)
    font=lambda n:ImageFont.truetype('C:/Windows/Fonts/arial.ttf',n)
    d.text((w/2,24),title,font=font(31),fill='#1d4249',anchor='mt')
    from cad.prototype_arm.build_linka_v1 import REVISION
    d.text((w/2,h-63),(revision or REVISION)+' / 150 + 120 mm',font=font(23),fill='#1d4249',anchor='mt')
    d.text((w/2,h-30),'Boyutlandirma prototipi: motor kulagi, insert ve yuk deneyi gerekli.',font=font(20),fill='#8a4b36',anchor='mt')
    im.save(path)
