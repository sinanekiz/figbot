import React from 'react';
import {labels, ranges} from './control.js';
export function JointPanel({pose, selected, onSelect, onChange, onBegin, onEnd, disabled, gripperAvailable = true}) {
  const slider = (i, jaw = false) => <input aria-label={labels[i] + ' açısı'} type="range" min={ranges[i][0]} max={ranges[i][1]} step=".005" value={pose[i]} disabled={disabled || i === 5 && !gripperAvailable}
    onPointerDown={onBegin} onPointerUp={onEnd} onPointerCancel={onEnd} onBlur={onEnd}
    onKeyDown={event => { if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End'].includes(event.key)) onBegin(); }} onKeyUp={onEnd}
    onChange={event => onChange(i, Number(event.target.value))} style={{'--fill': `${(pose[i] - ranges[i][0]) / (ranges[i][1] - ranges[i][0]) * 100}%`}}/>;
  return <><section><h2>Eklemler</h2>{labels.slice(0, 5).map((label, i) => <div className={'joint-row ' + (selected === i ? 'selected' : '')} key={label}>
    <button className="joint-label" onClick={() => onSelect(i)} aria-pressed={selected === i}>{label}</button>{slider(i)}<output>{Math.round(pose[i] * 180 / Math.PI)}°</output>
  </div>)}</section><section><h2>Kıskaç</h2>{slider(5, true)}{!gripperAvailable && <p className="note">Motor yok · Kavrama devre dışı</p>}<div className="jaw-labels"><span>Kapalı</span><span>Açık</span></div></section></>;
}
