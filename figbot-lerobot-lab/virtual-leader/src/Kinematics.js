import * as THREE from 'three';
import {names, clamp} from './control.js';

const quaternion = q => new THREE.Quaternion(q[1], q[2], q[3], q[0]).normalize();
const rotationError = (target, current) => {
  const q = target.clone().multiply(current.clone().invert()).normalize();
  if (q.w < 0) q.set(-q.x, -q.y, -q.z, -q.w);
  const sine = Math.hypot(q.x, q.y, q.z);
  const scale = sine < 1e-9 ? 2 : 2 * Math.atan2(sine, q.w) / sine;
  return [q.x * scale, q.y * scale, q.z * scale];
};

// A visual handle at the fixed finger tip, derived from the exact mesh vertices.
// This is not a physically calibrated tool center point.
export function fingerReference(model, geometry) {
  let visual;
  const find = body => {
    if (body.joint?.name === 'wrist_roll') visual = body.visuals.find(v => v.mesh === 'wrist_roll_follower_so101_v1.stl');
    body.children.forEach(find);
  };
  find(model);
  if (!visual) throw new Error('Sabit kıskaç modeli bulunamadı.');
  geometry.computeBoundingBox();
  const {min, max} = geometry.boundingBox;
  const threshold = max.z - (max.z - min.z) * .02;
  const vertices = geometry.getAttribute('position');
  const point = new THREE.Vector3(); let count = 0;
  for (let i = 0; i < vertices.count; i++) if (vertices.getZ(i) >= threshold) {
    point.add(new THREE.Vector3().fromBufferAttribute(vertices, i)); count++;
  }
  if (!count) throw new Error('Kıskaç ucu hesaplanamadı.');
  return point.divideScalar(count).applyQuaternion(quaternion(visual.quaternion)).add(new THREE.Vector3(...visual.position));
}

function linearSolve(matrix, rhs) {
  const rows = matrix.map((row, i) => [...row, rhs[i]]), n = rows.length;
  for (let column = 0; column < n; column++) {
    let pivot = column;
    for (let row = column + 1; row < n; row++) if (Math.abs(rows[row][column]) > Math.abs(rows[pivot][column])) pivot = row;
    if (Math.abs(rows[pivot][column]) < 1e-12) return Array(n).fill(0);
    [rows[pivot], rows[column]] = [rows[column], rows[pivot]];
    const divisor = rows[column][column];
    for (let j = column; j <= n; j++) rows[column][j] /= divisor;
    for (let row = 0; row < n; row++) if (row !== column) {
      const factor = rows[row][column];
      for (let j = column; j <= n; j++) rows[row][j] -= factor * rows[column][j];
    }
  }
  return rows.map(row => row[n]);
}

export class KinematicArm {
  constructor(model, reference) {
    this.root = new THREE.Group(); this.root.rotation.x = -Math.PI / 2;
    this.joints = []; this.limits = [];
    const create = (body, parent) => {
      const origin = new THREE.Group(); origin.position.fromArray(body.position); origin.quaternion.copy(quaternion(body.quaternion)); parent.add(origin);
      const pivot = new THREE.Group(); origin.add(pivot);
      if (body.joint) {
        const i = names.indexOf(body.joint.name);
        this.joints[i] = {pivot, axis: new THREE.Vector3(...body.joint.axis).normalize()};
        this.limits[i] = body.joint.range;
        if (i === 4) {
          this.tool = new THREE.Object3D(); this.tool.position.copy(reference); pivot.add(this.tool);
        }
      }
      body.children.forEach(child => create(child, pivot));
    };
    create(model, this.root);
    if (this.joints.length !== 6 || !this.tool) throw new Error('Altı eklemli SO101 modeli gerekli.');
  }
  forward(pose) {
    this.joints.forEach(({pivot, axis}, i) => pivot.quaternion.setFromAxisAngle(axis, pose[i]));
    this.root.updateMatrixWorld(true);
    return {position: this.tool.getWorldPosition(new THREE.Vector3()), orientation: this.tool.getWorldQuaternion(new THREE.Quaternion())};
  }
  solve(pose, target, orientation) {
    if (!target.toArray().every(Number.isFinite)) throw new Error('Sonlu kol hedefi gerekli.');
    const origin = [...pose], weight = .018, damping = .006, epsilon = 1e-5;
    // The five arm joints move together; jaw opening is excluded from the solve.
    const limits = this.limits.slice(0, 5).map(([lo, hi], i) => [Math.max(lo, origin[i] - .12), Math.min(hi, origin[i] + .12)]);
    const residual = value => {
      const frame = this.forward(value), position = target.clone().sub(frame.position).toArray();
      return [...position, ...rotationError(orientation, frame.orientation).map(v => v * weight)];
    };
    const cost = r => r.reduce((sum, v) => sum + v * v, 0);
    let result = [...pose], error = residual(result), best = cost(error);
    for (let iteration = 0; iteration < 28; iteration++) {
      const columns = Array.from({length: 5}, (_, i) => {
        const probe = [...result]; probe[i] += epsilon;
        const next = residual(probe);
        return error.map((v, k) => (v - next[k]) / epsilon);
      });
      const matrix = columns.map((a, i) => columns.map((b, j) => a.reduce((sum, v, k) => sum + v * b[k], 0) + (i === j ? damping * damping : 0)));
      const rhs = columns.map(column => column.reduce((sum, v, k) => sum + v * error[k], 0));
      const step = linearSolve(matrix, rhs);
      let improved = false;
      for (const fraction of [1, .5, .25, .125]) {
        const candidate = [...result];
        for (let i = 0; i < 5; i++) candidate[i] = clamp(result[i] + clamp(step[i], -.08, .08) * fraction, ...limits[i]);
        const nextError = residual(candidate), nextCost = cost(nextError);
        if (nextCost < best - 1e-14) {
          result = candidate; error = nextError; best = nextCost; improved = true; break;
        }
      }
      if (!improved || best < 1e-10) break;
    }
    const frame = this.forward(result);
    return {pose: result, error: frame.position.distanceTo(target)};
  }
}

export function screenDisplacement(camera, position, height, dx, dy, depth = false) {
  const scale = 2 * position.distanceTo(camera.position) * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) / Math.max(1, height);
  const right = new THREE.Vector3(1, 0, 0).applyQuaternion(camera.quaternion);
  const up = new THREE.Vector3(0, 1, 0).applyQuaternion(camera.quaternion);
  const forward = new THREE.Vector3(0, 0, -1).applyQuaternion(camera.quaternion);
  return right.multiplyScalar(clamp(dx, -24, 24) * scale).addScaledVector(depth ? forward : up, -clamp(dy, -24, 24) * scale);
}
