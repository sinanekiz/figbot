"""Robot-local XYZ -> joint pose -> concurrent servo motion.

Uses the existing vendor-URDF model and SciPy IK. The current map is a local,
supervised geometric estimate, not a calibrated phone/world transform. Wrist
roll is held at the measured angle; 4 axes solve position plus tool pitch.
"""
import json
import numpy as np
from scipy.optimize import least_squares
from .so101_kinematics import SO101Model
from .protocol import BusError


class CartesianController:
    def __init__(self, urdf, reference):
        self.model=SO101Model(urdf)
        self.reference=json.loads(reference.read_text(encoding='utf-8'))
        if self.reference['urdf_sha256']!=self.model.sha256:
            raise BusError('XYZ model/referans dosyaları uyuşmuyor.')
        self.raw0=np.array(self.reference['reference_raw_unwrapped'],dtype=float)
        self.q0=np.deg2rad(self.reference['reference_joint_degrees'])
        self.signs=np.array(self.reference['direction_signs'],dtype=float)
        if self.raw0.shape!=(5,) or self.q0.shape!=(5,) or self.signs.shape!=(5,) or not np.isin(self.signs,[-1,1]).all():
            raise BusError('XYZ referansı eksik.')

    def check(self, control):
        if self.reference['servo_offsets']!={str(i):v for i,v in control.offsets.items()}:
            raise BusError('XYZ kalibrasyon ofsetleri donanımla uyuşmuyor.')

    def angles(self, raw):
        delta=np.array(raw,dtype=float)-self.raw0
        if delta.shape!=(5,) or not np.isfinite(delta).all() or np.any(np.abs(delta)>=2048):
            raise BusError('XYZ enkoder dalı dışında; otomatik sarma yok.')
        return self.q0+self.signs*delta*(2*np.pi/4096)

    def pose(self, raw):
        return self.model.forward(self.angles(raw))['gripper_frame']

    def plan(self, control, xyz_mm):
        self.check(control)
        target=np.asarray(xyz_mm,dtype=float)
        if target.shape!=(3,) or not np.isfinite(target).all():
            raise BusError('Sonlu X,Y,Z milimetre koordinatları gerekli.')
        rows=control.read_all();control.validate_rows(rows)
        if any(abs(r['speed'])>50 for r in rows.values()):
            raise BusError('XYZ hesabı için önce hareketin tamamlanmasını bekle.')
        raw=np.array([rows[i]['position'] for i in range(1,6)],dtype=float)
        q=self.angles(raw);current=self.model.forward(q)['gripper_frame']
        axis=current[:3,2]
        pitch=np.arctan2(axis[2],np.linalg.norm(axis[:2]))
        lower=[];upper=[]
        for i in range(4):
            lo,hi=control.envelopes[i+1]
            ends=self.q0[i]+self.signs[i]*(np.array([lo,hi])-self.raw0[i])*(2*np.pi/4096)
            lower.append(max(min(ends),self.model.limits[i,0],q[i]-np.pi/2))
            upper.append(min(max(ends),self.model.limits[i,1],q[i]+np.pi/2))
        if np.any(q[:4]<lower) or np.any(q[:4]>upper):
            raise BusError('Mevcut duruş model/oturum aralığı dışında.')
        def full(q4):return np.r_[q4,q[4]]
        def residual(q4):
            tip=self.model.forward(full(q4))['gripper_frame'];a=tip[:3,2]
            angle=np.arctan2(a[2],np.linalg.norm(a[:2]))
            return np.r_[tip[:3,3]-target/1000,.1*(angle-pitch)]
        fit=least_squares(residual,q[:4],bounds=(lower,upper),max_nfev=160,
                          ftol=1e-10,xtol=1e-10,gtol=1e-10)
        solved=full(fit.x)
        counts=np.rint(self.raw0+self.signs*(solved-self.q0)*4096/(2*np.pi)).astype(int)
        counts[4]=int(raw[4])
        achieved=self.pose(counts)
        error=float(np.linalg.norm(achieved[:3,3]-target/1000)*1000)
        if not fit.success or error>2 or abs(residual(fit.x)[3])>.0035:
            raise BusError(f'XYZ hedefi seçilen yönelimle çözülemedi; hata {error:.1f} mm.')
        # Coarse table-plane exclusion, NOT complete collision detection.
        for alpha in np.linspace(0,1,41):
            frames=self.model.forward(q+alpha*(self.angles(counts)-q))
            if any(frames[name][2,3]<.030 for name in ('wrist_flex','gripper_frame')):
                raise BusError('Tahmini yol masa düzlemine çok yakın.')
        return {'positions':{str(i):int(counts[i-1]) for i in range(1,5)},
                'frame':'vendor_base_link','requested_xyz_mm':target.tolist(),
                'predicted_xyz_mm':(achieved[:3,3]*1000).tolist(),'model_error_mm':error,
                'calibration_status':self.reference['status'],
                'physical_accuracy_verified':False,'collision_checked':False}
