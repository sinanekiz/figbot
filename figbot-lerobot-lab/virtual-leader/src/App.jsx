import React, {useEffect, useRef, useState} from 'react';
import {RobotScene} from './RobotScene.js';
import {JointPanel} from './JointPanel.jsx';
import {API} from './api.js';
import {closedPose, clamp, ranges} from './control.js';

const api = new API();
const disconnected = {state: 'DISCONNECTED', message: 'Hazır · Gerçek kol bağlı değil', profile_verified: false, motors: {}, epoch: 0};
const locked = value => value.state !== 'DISCONNECTED' && (value.state.startsWith('FAULT') || value.emergency_latched || value.thermal_latched);

export default function App() {
  const [pose, setPose] = useState([...closedPose]), [selected, setSelected] = useState(1);
  const [status, setStatus] = useState(disconnected), [error, setError] = useState('');
  const [ikNote, setIkNote] = useState('Kolun ucu · Birlikte hareket');
  const [ports, setPorts] = useState([]), [port, setPort] = useState('COM5');
  const [busy, setBusy] = useState(false), [ready, setReady] = useState(false), [stopped, setStopped] = useState(false), [help, setHelp] = useState(false);
  const host = useRef(), scene = useRef(), latest = useRef({pose: [...closedPose], status: disconnected, gesture: false, stopped: false, sequence: 0, inFlight: false, generation: 0, independentHomeView: false, homeEpoch: null});
  const connected = status.state !== 'DISCONNECTED', active = status.state === 'ACTIVE';
  const accept = value => {
    if (value.server_session === latest.current.status.server_session && value.state_revision < latest.current.status.state_revision) return false;
    if (value.state === 'ACTIVE' && latest.current.status.state === 'ACTIVE' && value.epoch < latest.current.status.epoch) return false;
    const previous = latest.current.status;
    latest.current.status = value; setStatus(value);
    scene.current?.setDisabledJoints(value.gripper_available === false ? [5] : []);
    if (latest.current.transportError) { latest.current.transportError = false; setError(''); }
    if (value.state !== 'ACTIVE') latest.current.gesture = false;
    if (value.state === 'DISCONNECTED' || value.state === 'CONNECTED' && previous.state === 'DISCONNECTED') latest.current.homeEpoch = null;
    if (value.connection_recovering || locked(value) || value.state === 'ACTIVE' && previous.state === 'ACTIVE' && value.epoch !== previous.epoch) {
      latest.current.gesture = false; latest.current.generation++; scene.current?.end();
    }
    if (value.home_completed_epoch != null && value.home_completed_epoch !== latest.current.homeEpoch) {
      latest.current.homeEpoch = value.home_completed_epoch; latest.current.independentHomeView = false;
    }
    return true;
  };
  const updatePose = (value, independent = false) => {
    const bounds = latest.current.status.trial_bounds;
    const next = bounds && !independent ? value.map((v, i) => clamp(v, Math.max(ranges[i][0], bounds[i][0]), Math.min(ranges[i][1], bounds[i][1]))) : [...value];
    if (latest.current.status.gripper_available === false) next[5] = latest.current.pose[5];
    latest.current.pose = next; setPose(next); scene.current?.setPose(next);
  };
  const canMove = () => ready && !latest.current.stopped && !latest.current.status.homing && !latest.current.status.connection_recovering && !locked(latest.current.status);
  const begin = () => { if (canMove()) {
    if (latest.current.independentHomeView && latest.current.status.angles) updatePose(latest.current.status.angles);
    latest.current.independentHomeView = false; latest.current.gesture = true;
  } };
  const end = async () => {
    const r = latest.current;
    const hadGesture = r.gesture; r.gesture = false; r.generation++;
    if (r.holdPromise) return r.holdPromise;
    if (hadGesture && latest.current.status.state === 'ACTIVE') {
      r.holdPromise = (async () => {
        try { const value = await api.action('hold'); if (accept(value) && value.angles && !r.independentHomeView && !locked(value)) updatePose(value.angles); }
        catch (e) { setError(e.message); }
        finally { r.holdPromise = null; }
      })();
      return r.holdPromise;
    }
  };
  const perform = async (route, value = {}) => {
    setBusy(true); setError('');
    try {
      if (route === 'disconnect') {
        latest.current.gesture = false; latest.current.generation++; scene.current?.end();
      } else await end();
      if (route === 'activate_trial' || route === 'disconnect') latest.current.homeEpoch = null;
      const next = await api.action(route, value); if (!accept(next)) return;
      if (next.angles && ['connect', 'activate', 'activate_trial', 'hold'].includes(route)) updatePose(next.angles);
      if (route === 'activate' || route === 'activate_trial' || route === 'disconnect') { latest.current.stopped = false; setStopped(false); }
      return next;
    } catch (e) { setError(e.message); } finally { setBusy(false); }
  };
  const stop = async () => {
    latest.current.gesture = false; latest.current.generation++; latest.current.stopped = true; setStopped(true); scene.current?.end();
    if (latest.current.status.state !== 'DISCONNECTED') {
      setError('');
      try { accept(await api.action('emergency', {port})); }
      catch (e) { setError('Torkun kapandığı doğrulanamadı: ' + e.message + ' Motor beslemesini kapatın.'); }
    }
  };
  const returnClosed = async () => {
    const before = [...latest.current.pose];
    await end(); scene.current?.end();
    latest.current.independentHomeView = true;
    updatePose(latest.current.status.closed_home_angles || closedPose, true);
    if (latest.current.status.state !== 'DISCONNECTED') await perform('home', {angles: before});
  };
  const releaseTorque = async () => {
    const r = latest.current;
    r.gesture = false; r.generation++; r.stopped = true; setStopped(true); scene.current?.end();
    setBusy(true); setError('');
    try { accept(await api.action('emergency', {port})); }
    catch (e) { setError('Torkun kapandığı doğrulanamadı: ' + e.message + ' Motor beslemesini kapatın.'); }
    finally { setBusy(false); }
  };

  useEffect(() => {
    let mounted = true, firstRefresh = true;
    const refresh = async () => {
      try { const value = await api.state(); if (mounted) {
        if (!accept(value)) return;
        if (firstRefresh && !value.angles) updatePose(value.closed_home_angles || closedPose, true);
        firstRefresh = false;
        if (value.homing || latest.current.independentHomeView) updatePose(value.home_angles || value.closed_home_angles || closedPose, true);
        else if (value.state === 'ACTIVE' && !latest.current.gesture && value.angles && !value.connection_recovering) updatePose(value.angles);
      } }
      catch (e) { if (mounted) { latest.current.transportError = true; setError(e.message); } } // a later successful poll clears this transport error
    };
    refresh();
    fetch('/api/ports').then(r => r.json()).then(value => { if (mounted) { setPorts(value.ports); if (value.ports.length && !value.ports.some(p => p.device === 'COM5')) setPort(value.ports[0].device); } }).catch(e => setError(e.message));
    const poll = setInterval(refresh, 300);
    const transmit = setInterval(async () => {
      const r = latest.current;
      if (r.inFlight || r.stopped) return;
      if (r.status.state === 'ACTIVE' && r.gesture) {
        r.inFlight = true; const generation = r.generation;
        try {
          const result = await api.action('target', {angles: r.pose, epoch: r.status.epoch, sequence: ++r.sequence, gesture: true});
          if (mounted && generation === r.generation) accept(result);
        } catch (e) {
          if (generation === r.generation && mounted) { r.transportError = e.name === 'TypeError' || e.name === 'TimeoutError'; setError(e.message); r.gesture = false; scene.current?.end(); api.action('hold').then(accept).catch(() => {}); }
        } finally { r.inFlight = false; }
      } else if (r.status.recording && r.status.state !== 'ACTIVE') {
        r.inFlight = true;
        try { await api.action('record/simulation', {angles: r.pose, sequence: ++r.sequence}); }
        catch (e) { if (mounted) setError(e.message); }
        finally { r.inFlight = false; }
      }
    }, 100);
    const pause = () => { scene.current?.end(); end(); };
    const key = event => { if (event.code === 'Space' && !['INPUT', 'SELECT', 'BUTTON', 'TEXTAREA'].includes(event.target.tagName)) { event.preventDefault(); stop(); } if (event.key === 'Escape') pause(); };
    const visibility = () => { if (document.hidden) pause(); };
    window.addEventListener('blur', pause); window.addEventListener('keydown', key); document.addEventListener('visibilitychange', visibility);
    return () => { mounted = false; clearInterval(poll); clearInterval(transmit); window.removeEventListener('blur', pause); window.removeEventListener('keydown', key); document.removeEventListener('visibilitychange', visibility); };
  }, []);

  useEffect(() => {
    let valid = true;
    const view = new RobotScene(host.current, {
      select: setSelected, change: updatePose, ik: setIkNote,
      canMove: () => !latest.current.stopped && !latest.current.status.homing && !latest.current.status.connection_recovering && !locked(latest.current.status),
      begin: () => {
        if (latest.current.independentHomeView && latest.current.status.angles) updatePose(latest.current.status.angles);
        latest.current.independentHomeView = false; latest.current.gesture = true;
      }, end,
      ready: () => { if (valid) setReady(true); }, error: message => { if (valid) setError(message); },
    });
    scene.current = view; view.setDisabledJoints(latest.current.status.gripper_available === false ? [5] : []); view.setPose(latest.current.pose);
    return () => { valid = false; view.dispose(); };
  }, []);

  const choose = i => { setSelected(i); scene.current?.select(i); };
  const slide = (i, angle) => { if (!canMove() || i === 5 && latest.current.status.gripper_available === false) return; const next = [...latest.current.pose]; next[i] = clamp(angle, ...ranges[i]); updatePose(next); };
  const trial = status.control_mode === 'RELATIVE_TRIAL';
  const mode = status.thermal_latched ? 'Sıcaklık kesmesi' : status.emergency_latched ? 'Motor torku kapalı' : status.connection_recovering ? 'Motor yanıtı bekleniyor' : active ? (trial ? 'Tam hız kontrolü açık' : 'Gerçek kol etkin') : 'Simülasyon';
  return <div className="app-shell">
    <header><h1>FIGBOT · Sanal sürücü</h1><div className="header-controls"><span className="mode"><i className={active ? 'live-dot' : ''}/>{mode}</span><button onClick={() => document.getElementById('hardware').scrollIntoView({behavior: 'smooth'})}>Gerçek kol</button><button className="stop" onClick={stop}>■ &nbsp; Durdur</button></div></header>
    <main><div className="viewport"><div ref={host} className="scene" data-testid="robot-scene"/><div className="viewport-top"><span>{ikNote}</span><button onClick={() => scene.current?.resetView()}>↶ &nbsp; Görünümü sıfırla</button></div>
      {!ready && <div className="overlay">SO101 modeli yükleniyor…</div>}
      {stopped && <div className="overlay stopped"><strong>Kontrol durduruldu</strong>{!active && !locked(status) && <button onClick={() => { latest.current.stopped = false; setStopped(false); }}>Simülasyona devam et</button>}</div>}
      <div className="mouse-hints"><span>Sol tuş · Kolun ucunu taşı</span><span>{status.gripper_available === false ? 'Kıskaç yok · Tekerlek kapalı' : 'Tekerlek · Aşağı aç / Yukarı kapat'}</span><span>Sağ tuş · Görünümü döndür</span><span>Z + sol · Yalnız bilek</span><span>Shift + sol · Derinlik</span></div>
    </div><aside>
      <JointPanel pose={pose} selected={selected} onSelect={choose} onChange={slide} onBegin={begin} onEnd={end} gripperAvailable={status.gripper_available !== false} disabled={!ready || stopped || status.homing || status.connection_recovering || locked(status)}/>
      <section id="hardware"><h2>Gerçek kol</h2><div className="port-row"><label htmlFor="port">Port</label><select id="port" value={port} onChange={event => setPort(event.target.value)} disabled={connected || busy}>{ports.length ? ports.map(p => <option key={p.device} value={p.device}>{p.device}</option>) : <option value="COM5">COM5 · Bağlı değil</option>}</select></div>
        {status.gripper_available === false && <p className="note">5 motor · Görev: incirin yanına yaklaşma. Kavrama komutu gönderilmez.</p>}
        {status.hardware_replacement?.status === 'PENDING_PHYSICAL_ID_VERIFICATION' && <p className="note">ID6 → ID4 değişimi bekliyor · Motor yanıtı henüz alınamadı.</p>}
        <button className="outline full" disabled={busy || active} onClick={() => connected ? perform('disconnect') : perform('connect', {port})}>{connected ? 'Bağlantıyı kapat' : 'Pozu oku'}</button>
        <p className="note">Önce gerçek kolun konumu alınır.</p>
        {!status.profile_verified && <button className="text-button" onClick={() => setHelp(!help)}>Fiziksel eşleme gerekli ⓘ</button>}
        {help && <p className="note help">Her eklemin modeldeki sıfırı, motor yönü, çalışma sınırları ve mevcut ofseti doğrulanmalı. SANAL_SURUCU.md adımları açıklar. Simülasyon eşleme gerektirmez.</p>}
        {Object.keys(status.motors).length > 0 && <><div className="readback" aria-label="Motor konumları ve sıcaklıkları">{Object.entries(status.motors).map(([id, motor]) => <span key={id} className={motor.temperature >= 55 ? 'hot-motor' : ''}>M{id} <strong>{motor.position}</strong><br/><b>{motor.temperature}°C</b> · {motor.voltage} V</span>)}</div><p className="note">{status.sample_age_s == null || status.sample_age_s > 2 ? 'Son ölçüm güncel değil.' : 'Canlı ölçüm'} · 55°C: tork kesilir · Yeniden açılış: en fazla 45°C</p></>}
        <button className="stop full" onClick={releaseTorque}>Motor torkunu kapat</button>
        <p className="note">Tork kapanınca kol kendi ağırlığıyla düşebilir. Bu düğme elektrik beslemesini kesmez.</p>
        <button className="primary full" disabled={busy || !ready || !connected || status.connection_recovering || status.state.startsWith('FAULT') || locked(status) && (!status.torque_release_confirmed || Object.values(status.motors).some(m => m.temperature > 45) || status.sample_age_s > 2)} onClick={() => active ? perform('hold') : status.profile_verified ? perform('activate') : perform('activate_trial', {angles: latest.current.pose})}>{active ? 'Pozu tut' : status.profile_verified ? '▶　Kontrolü başlat' : '▶　Deneme kontrolünü başlat'}</button>
        <button className="outline full" disabled={busy || !ready || status.homing || status.connection_recovering || locked(status) || connected && status.physical_home_available === false} onClick={returnClosed}>{status.homing ? 'Kapalı poza dönüyor…' : '↶　Başlangıca dön'}</button>
        <p className="note">{status.physical_home_available === false ? 'Motor değişti: gerçek kapalı poz kaydı yenilenmeli. Bağlı değilken bu düğme yalnız modeli sıfırlar.' : 'Başlangıç: kolun kapalı pozu. Model ve gerçek kol kendi kayıtlı kapalı pozlarına döner; göreli eşleme yeniden kurulur.'}</p>
        {!status.profile_verified && <p className="note">Tam hız · Başlangıca bağlı hareket sınırı kaldırıldı. Motorların kayıtlı konum aralığı kullanılır. Fiziksel yön eşlemesi henüz doğrulanmadı.</p>}
      </section>
      <section className="record"><h2>Gösterim kaydı</h2><button className="full" disabled={busy || !ready} onClick={() => perform(status.recording ? 'record/stop' : 'record/start')}>{status.recording ? '■　Kaydı bitir' : '▶　Kaydı başlat'}</button>{status.recording && <p className="note recording">Kayıt sürüyor · {status.record_count} olay</p>}{status.last_recording && !status.recording && <p className="note saved">Kaydedildi: {status.last_recording.split(/[\\/]/).pop()}</p>}<p className="note">{active ? 'Gerçek komutlar ve motor ölçümleri kaydedilir.' : 'Simülasyon kaydı · Kamera içermez.'}</p></section>
      {!connected && <button className="text-button reset" disabled={stopped || !ready} onClick={async () => { await end(); updatePose(closedPose, true); }}>Sanal pozu sıfırla</button>}
    </aside></main>
    <footer role="status"><i className={error || locked(status) ? 'error-dot' : ''}/><span>{locked(status) ? status.message : error || status.message}</span><span className="footer-help">Shift + tekerlek: yakınlaştır · Boşluk: durdur</span></footer>
  </div>;
}
