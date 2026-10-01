"""Windows camera opening with backend support checks and first-frame validation."""
import cv2

def open_camera(index, mode='Otomatik', cancelled=lambda:False, report=lambda value:None, cv=cv2):
    if not 0<=index<=9:raise ValueError('Kamera numarası 0–9 olmalı.')
    candidates=[('Windows / MSMF',cv.CAP_MSMF),('DirectShow',cv.CAP_DSHOW)]
    if mode!='Otomatik':candidates=[pair for pair in candidates if pair[0]==mode]
    if not candidates:raise ValueError('Bilinmeyen kamera bağlantısı.')
    errors=[]
    for name,backend in candidates:
        if cancelled():raise RuntimeError('Kamera açma iptal edildi.')
        if not cv.videoio_registry.hasBackend(backend):
            errors.append(name+' desteği kurulu değil');continue
        report(f'Kamera {index}: {name} deneniyor…')
        cap=cv.VideoCapture(index,backend)
        keep=False
        try:
            if cancelled():raise RuntimeError('Kamera açma iptal edildi.')
            if not cap.isOpened():
                errors.append(name+' aygıtı açamadı');continue
            ok,frame=cap.read()
            if cancelled():raise RuntimeError('Kamera açma iptal edildi.')
            if not ok or frame is None:
                errors.append(name+' görüntü vermedi');continue
            keep=True
            return cap,frame,name
        finally:
            if not keep:cap.release()
    raise RuntimeError('; '.join(errors)+'. Windows Kamera gizliliğinde masaüstü uygulama iznini, seçilen kamera numarasını ve başka uygulamanın kamerayı kullanıp kullanmadığını kontrol et.')
