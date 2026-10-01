export const names = ['shoulder_pan', 'shoulder_lift', 'elbow_flex', 'wrist_flex', 'wrist_roll', 'gripper'];
export const labels = ['Taban', 'Omuz', 'Dirsek', 'Bilek', 'Bilek dönüşü', 'Kıskaç'];
export const initialPose = [0, -.35, .78, .17, 0, .4];
export const closedPose = [.030138, -1.745329, 1.565, 1.331938, 1.561153, -.144532];
export const ranges = [[-1.919862, 1.919862], [-1.745329, 1.745329], [-1.69, 1.69], [-1.658062, 1.658062], [-2.743847, 2.841206], [-.174532, 1.745329]];
export const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
export function scrollJaw(pose, pixels) {
  const next = [...pose];
  next[5] = clamp(next[5] + clamp(pixels, -120, 120) * .0008, ...ranges[5]);
  return next;
}
