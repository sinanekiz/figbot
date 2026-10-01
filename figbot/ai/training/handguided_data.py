"""Offline review and corrected targets for passive demonstrations; no robot I/O."""
import hashlib
import json
from pathlib import Path
import numpy as np


def corrected_targets(times, positions, cycles, open_count):
    """Keep arm geometry; remove <=3-count jitter and standardize open phases.

    Synthetic gripper targets do not imply physically tested jaw clearance.
    Cycle fields: start, close_start, close_end, release_start, release_end, end.
    """
    q = np.asarray(positions, dtype=float)
    t = np.asarray(times, dtype=float)
    if q.shape != (len(t), 6) or np.any(np.diff(t) <= 0):
        raise ValueError('Strictly increasing timestamps and six joints required')
    if not q[:, 5].min() <= open_count <= q[:, 5].max():
        raise ValueError('Opening must stay inside the observed encoder range')
    clean = q.copy()
    padded = np.pad(q[:, :5], ((1, 1), (0, 0)), mode='edge')
    median = np.median(np.stack([padded[i:i+len(q)] for i in range(3)]), axis=0)
    clean[:, :5] = np.where(abs(median-q[:, :5]) <= 3, median, q[:, :5])
    group = np.full(len(t), -1, dtype=int)
    phase = np.full(len(t), 'excluded', dtype='<U12')
    for i, c in enumerate(cycles):
        a, b, d, e, f, z = [c[k] for k in
            ('start', 'close_start', 'close_end', 'release_start', 'release_end', 'end')]
        if not a < b < d < e < f <= z:
            raise ValueError('Invalid phase chronology')
        active = (t >= a) & (t < z)
        if np.any(group[active] >= 0):
            raise ValueError('Cycles overlap')
        group[active] = i
        masks = [(active & (t < b), 'approach'),
                 (active & (t >= b) & (t < d), 'grasp'),
                 (active & (t >= d) & (t < e), 'carry'),
                 (active & (t >= e) & (t < f), 'release'),
                 (active & (t >= f), 'open')]
        for mask, name in masks:
            phase[mask] = name
        # Preserve the measured held width; each fig can have a different width.
        held = (t >= d) & (t < e)
        if not held.any():
            raise ValueError('Missing held-grasp samples')
        grip = float(np.median(q[held, 5]))
        clean[active, 5] = np.interp(t[active], [a, b, d, e, f, z],
                                   [open_count, open_count, grip, grip, open_count, open_count])
    return clean, group, phase


def suspect_intervals(times, positions, velocity_limit=1200., padding=.35):
    """Conservative data-quality flags, NOT a physical safety speed limit."""
    t = np.asarray(times)
    speed = abs(np.diff(positions[:, :5], axis=0)) / np.diff(t)[:, None]
    bad = np.flatnonzero(speed.max(axis=1) > velocity_limit)
    intervals = []
    for i in bad:
        a, b = float(t[i]-padding), float(t[i+1]+padding)
        if intervals and a <= intervals[-1][1]:
            intervals[-1][1] = max(intervals[-1][1], b)
        else:
            intervals.append([a, b])
    return intervals


def eligible(times, groups, intervals, history=.2, horizon=.6):
    """All history/action times must stay in one cycle, clear of suspect spans."""
    t = np.asarray(times)
    mask = np.zeros(len(t), dtype=bool)
    for g in np.unique(groups):
        if g < 0:
            continue
        ix = np.flatnonzero(groups == g)
        mask[ix] = (t[ix]-history >= t[ix[0]]) & (t[ix]+horizon <= t[ix[-1]])
    for a, b in intervals:
        mask &= ~((t-history <= b) & (t+horizon >= a))
    return mask


def prepare(episode, annotations, output):
    import cv2
    episode, output = Path(episode), Path(output)
    output.mkdir(parents=True, exist_ok=False)
    outcome = json.loads((episode/'outcome.json').read_text())
    if outcome.get('outcome') != 'SUCCESSFUL_MANUAL_DEMONSTRATION':
        raise ValueError('Explicit successful user outcome required')
    if json.loads((episode/'status.json').read_text())['state'] != 'STOPPED':
        raise ValueError('Only closed recordings can be used')
    rows = [json.loads(l) for l in (episode/'episode/samples.jsonl').read_text().splitlines()]
    timing = [json.loads(l) for l in (episode/'timing.jsonl').read_text().splitlines()]
    if len(rows) != len(timing):
        raise ValueError('Timing/sample count mismatch')
    motors = [sorted(r['motor_readings'], key=lambda v: v['id']) for r in rows]
    if any([r['id'] for r in v] != list(range(1, 7)) or any(r['torque'] != 0 for r in v) for v in motors):
        raise ValueError('Incomplete or powered observations')
    q = np.array([[r['position'] for r in v] for v in motors], dtype=float)
    elapsed = np.array([r['elapsed_seconds'] for r in rows])
    enc = np.array([(v['encoder_read_start']+v['encoder_read_end'])/2 for v in timing])
    capture = np.array([v['estimated_capture_monotonic'] for v in timing])
    offset = float(np.median(enc-elapsed))
    t = enc-offset
    frame_t = capture-offset
    if np.any(np.diff(enc) <= 0) or np.any(np.diff(capture) <= 0):
        raise ValueError('Nonmonotonic camera or encoder clock')
    if max(abs(capture-enc)) > .2:
        raise ValueError('Camera/encoder separation exceeds acquisition gate')
    clean, groups, phase = corrected_targets(t, q, annotations['cycles'], annotations['open_count'])
    intervals = suspect_intervals(t, q) + annotations.get('exclude_intervals', [])
    intervals += [[float(t[i]), float(t[i+1])] for i in np.flatnonzero(np.diff(t) > .25)]
    # Images are aligned to camera time; raw observations are interpolated, not edited.
    frame_groups = np.full(len(t), -1)
    for i, c in enumerate(annotations['cycles']):
        frame_groups[(frame_t >= c['start']) & (frame_t < c['end'])] = i
    valid = eligible(frame_t, frame_groups, intervals)
    history = np.stack([np.stack([np.interp(frame_t-d, t, q[:, j]) for j in range(6)], 1)
                        for d in [.2, .1, 0]], 1)
    current = history[:, -1]
    target = np.stack([np.stack([np.interp(frame_t+d, t, clean[:, j]) for j in range(6)], 1)
                       for d in [.2, .4, .6]], 1)
    cap = cv2.VideoCapture(str(episode/'episode/camera.avi'))
    images = []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        images.append(cv2.cvtColor(cv2.resize(frame, (128, 96)), cv2.COLOR_BGR2RGB))
    cap.release()
    if len(images) != len(rows):
        raise ValueError('Video count mismatch')
    np.savez_compressed(output/'dataset.npz', images=np.asarray(images)[valid],
        history=history[valid].astype('float32'), target=target[valid].astype('float32'),
        current=current[valid].astype('float32'), group=frame_groups[valid], times=frame_t[valid])
    with (output/'corrected_targets.jsonl').open('w') as stream:
        for i in range(len(t)):
            stream.write(json.dumps(dict(time=float(t[i]),raw=q[i].tolist(),corrected=clean[i].tolist(),
                phase=str(phase[i]),cycle=int(groups[i]),synthetic_gripper_target=True))+'\n')
    hashes = {str(f.relative_to(episode)):hashlib.sha256(f.read_bytes()).hexdigest()
              for f in [episode/'episode/camera.avi', episode/'episode/samples.jsonl', episode/'timing.jsonl']}
    report = dict(raw_frames=len(rows),retained_samples=int(valid.sum()),
        samples_per_cycle={str(g):int(sum(frame_groups[valid] == g)) for g in range(4)},
        excluded_suspect_intervals=intervals,source_hashes=hashes,
        corrections=annotations,source=str(episode),original_observations_preserved=True,
        action_source='CORRECTED_FUTURE_MEASURED_POSITIONS_NOT_LEADER_COMMANDS',
        autonomous_replay_allowed=False,physical_validation='UNVERIFIED')
    (output/'data_review.json').write_text(json.dumps(report,indent=2))
    return report


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--episode',type=Path,required=True)
    parser.add_argument('--annotations',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(prepare(args.episode,json.loads(args.annotations.read_text()),args.output),indent=2))
