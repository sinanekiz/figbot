import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {STLLoader} from 'three/addons/loaders/STLLoader.js';
import {scrollJaw, names, ranges, clamp} from './control.js';
import {KinematicArm, fingerReference, screenDisplacement} from './Kinematics.js';

export function createViewControls(camera, element) {
  const controls = new OrbitControls(camera, element);
  controls.mouseButtons = {LEFT: -1, MIDDLE: THREE.MOUSE.ROTATE, RIGHT: THREE.MOUSE.ROTATE};
  controls.enableZoom = false; controls.enablePan = false; controls.enableDamping = false;
  controls.minDistance = .22; controls.maxDistance = 1.5;
  controls.maxPolarAngle = Math.PI * .49;
  return controls;
}

export class RobotScene {
  constructor(host, callbacks) {
    this.host = host; this.callbacks = callbacks; this.selected = 1;
    this.pose = [0, 0, 0, 0, 0, 0]; this.joints = new Map(); this.markers = [];
    this.scene = new THREE.Scene(); this.scene.background = new THREE.Color('#a6acb4');
    this.camera = new THREE.PerspectiveCamera(36, 1, .001, 6);
    this.renderer = new THREE.WebGLRenderer({antialias: true});
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFShadowMap;
    host.appendChild(this.renderer.domElement);
    this.renderer.domElement.setAttribute('aria-label', 'SO101 üç boyutlu kol. Sol tuş kolun ucu, Z ve sol tuş yalnız bilek, tekerlek kıskaç, sağ tuş görünüm.');
    this.renderer.domElement.tabIndex = 0;
    this.controls = createViewControls(this.camera, this.renderer.domElement);
    this.resetView();
    this.scene.add(new THREE.HemisphereLight(0xffffff, 0x68717f, 1.6));
    const sun = new THREE.DirectionalLight(0xffffff, 1.8);
    sun.position.set(.3, .65, .4); sun.castShadow = true;
    sun.shadow.mapSize.set(2048, 2048);
    Object.assign(sun.shadow.camera, {left: -.5, right: .5, top: .5, bottom: -.5, near: .01, far: 2});
    sun.shadow.bias = -.0003; this.scene.add(sun);
    const ground = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), new THREE.MeshStandardMaterial({color: '#a6acb4', roughness: 1}));
    ground.rotation.x = -Math.PI / 2; ground.position.y = -.006; ground.receiveShadow = true; this.scene.add(ground);
    const grid = new THREE.GridHelper(2, 40, '#c3c8cf', '#bdc2ca'); grid.position.y = -.0055;
    grid.material.transparent = true; grid.material.opacity = .45; this.scene.add(grid);
    this.root = new THREE.Group(); this.root.rotation.x = -Math.PI / 2; this.scene.add(this.root);
    this.bind();
    this.resizeObserver = new ResizeObserver(() => this.resize()); this.resizeObserver.observe(host);
    this.resize();
    this.frame = null;
    const render = () => { this.controls.update(); this.renderer.render(this.scene, this.camera); this.frame = requestAnimationFrame(render); };
    render();
    this.ready = this.load().then(() => { this.setPose(this.pose); this.select(this.selected); this.resetView(); callbacks.ready?.(); })
      .catch(error => callbacks.error?.('3D model yüklenemedi: ' + error.message));
  }

  resetView() {
    const bounds = new THREE.Box3().setFromObject(this.root || this.scene);
    if (!this.geometries || bounds.isEmpty()) {
      this.camera.position.set(.55, .38, .55);
      this.controls.target.set(.03, .145, 0); this.controls.update();
      return;
    }
    const center = bounds.getCenter(new THREE.Vector3());
    const direction = new THREE.Vector3(.8, .45, 1).normalize();
    this.camera.position.copy(center).add(direction);
    this.camera.lookAt(center);
    const inverse = this.camera.quaternion.clone().invert();
    const vertical = Math.tan(THREE.MathUtils.degToRad(this.camera.fov / 2));
    const horizontal = vertical * this.camera.aspect;
    let distance = .3;
    for (const x of [bounds.min.x, bounds.max.x]) for (const y of [bounds.min.y, bounds.max.y]) for (const z of [bounds.min.z, bounds.max.z]) {
      const point = new THREE.Vector3(x, y, z).sub(center).applyQuaternion(inverse);
      distance = Math.max(distance, point.z + Math.abs(point.x) / horizontal, point.z + Math.abs(point.y) / vertical);
    }
    this.camera.position.copy(center).addScaledVector(direction, distance * 1.16);
    this.controls.target.copy(center); this.controls.update();
  }
  resize() {
    const width = Math.max(1, this.host.clientWidth), height = Math.max(1, this.host.clientHeight);
    this.camera.aspect = width / height; this.camera.updateProjectionMatrix(); this.renderer.setSize(width, height);
    if (this.geometries) this.resetView();
  }
  async load() {
    const response = await fetch('/robot/model.json');
    if (!response.ok) throw new Error('SO101 geometrisi bulunamadı');
    const model = await response.json();
    const filenames = new Set();
    const gather = body => { body.visuals.forEach(v => filenames.add(v.mesh)); body.children.forEach(gather); };
    gather(model);
    const loader = new STLLoader();
    const geometries = new Map(await Promise.all([...filenames].map(async file => [file, await loader.loadAsync('/robot/' + file)])));
    this.geometries = geometries;
    const quaternion = q => new THREE.Quaternion(q[1], q[2], q[3], q[0]).normalize();
    const create = (body, parent, inheritedJoint = -1) => {
      const origin = new THREE.Group(); origin.position.fromArray(body.position); origin.quaternion.copy(quaternion(body.quaternion)); parent.add(origin);
      const pivot = new THREE.Group(); origin.add(pivot);
      let joint = inheritedJoint;
      if (body.joint) {
        joint = names.indexOf(body.joint.name);
        this.joints.set(body.joint.name, {pivot, axis: new THREE.Vector3(...body.joint.axis).normalize()});
        const marker = new THREE.Mesh(new THREE.TorusGeometry(joint === 0 ? .029 : .022, .0016, 8, 44),
          new THREE.MeshBasicMaterial({color: '#12bb7b'}));
        marker.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), new THREE.Vector3(...body.joint.axis).normalize());
        marker.userData.joint = joint; pivot.add(marker); this.markers.push(marker);
      }
      for (const visual of body.visuals) {
        const material = new THREE.MeshStandardMaterial({color: visual.motor ? '#252b32' : '#2478b5', metalness: visual.motor ? .35 : .12, roughness: .5});
        const mesh = new THREE.Mesh(geometries.get(visual.mesh), material);
        mesh.position.fromArray(visual.position); mesh.quaternion.copy(quaternion(visual.quaternion));
        mesh.castShadow = true; mesh.receiveShadow = true; mesh.userData.joint = joint; pivot.add(mesh);
      }
      body.children.forEach(child => create(child, pivot, joint));
    };
    create(model, this.root);
    const reference = fingerReference(model, geometries.get('wrist_roll_follower_so101_v1.stl'));
    this.kinematics = new KinematicArm(model, reference);
    this.handle = new THREE.Mesh(new THREE.SphereGeometry(.0045, 16, 12), new THREE.MeshBasicMaterial({color: '#00ff9d', depthTest: false}));
    this.handle.position.copy(reference); this.handle.renderOrder = 10;
    this.joints.get('wrist_roll').pivot.add(this.handle);
  }
  setPose(pose) {
    this.pose = [...pose];
    names.forEach((name, i) => { const joint = this.joints.get(name); if (joint) joint.pivot.quaternion.setFromAxisAngle(joint.axis, pose[i]); });
  }
  select(joint) {
    this.selected = joint;
    this.markers.forEach(marker => {
      marker.material.color.set(marker.userData.joint === joint ? '#00ff9d' : '#159463');
      marker.material.transparent = true; marker.material.opacity = marker.userData.joint === joint ? 1 : .55;
    });
  }
  setDisabledJoints(joints) {
    this.disabledJoints = new Set(joints);
    if (this.disabledJoints.has(5) && this.wheelActive) this.end();
  }
  moveTip(dx, dy, depth) {
    const frame = this.kinematics.forward(this.pose);
    const delta = screenDisplacement(this.camera, frame.position, this.host.clientHeight, dx, dy, depth);
    const target = frame.position.clone().add(delta);
    const result = this.kinematics.solve(this.pose, target, this.drag.orientation);
    this.callbacks.ik?.(result.error > .004 ? 'Uzanma sınırı · Hareket sınırlı' : 'Kolun ucu · Birlikte hareket');
    return result.pose;
  }
  bind() {
    const element = this.renderer.domElement;
    this.wristMode = false;
    const isZ = event => event.code === 'KeyZ' || event.key?.toLowerCase() === 'z';
    this.keyHandlers = {
      keydown: event => {
        if (!isZ(event) || ['INPUT', 'SELECT', 'TEXTAREA'].includes(event.target?.tagName) || event.target?.isContentEditable) return;
        this.wristMode = true;
        this.callbacks.ik?.('Z · Yalnız bilek · Yukarı/aşağı sürükle');
      },
      keyup: event => {
        if (!isZ(event)) return;
        this.wristMode = false;
        if (this.drag) this.drag.orientation = this.kinematics.forward(this.pose).orientation;
        this.callbacks.ik?.('Kolun ucu · Birlikte hareket');
      },
      blur: () => { this.wristMode = false; this.end(); this.callbacks.ik?.('Kolun ucu · Birlikte hareket'); },
    };
    if (typeof window !== 'undefined') Object.entries(this.keyHandlers).forEach(([name, handler]) => window.addEventListener(name, handler));
    this.handlers = {
      contextmenu: event => event.preventDefault(),
      pointerdown: event => {
        if (event.button !== 0 || !this.kinematics) return;
        if (!this.callbacks.canMove()) return;
        this.end();
        event.preventDefault(); element.focus();
        this.callbacks.begin();
        this.drag = {id: event.pointerId, x: event.clientX, y: event.clientY, orientation: this.kinematics.forward(this.pose).orientation};
        element.setPointerCapture(event.pointerId); element.classList.add('dragging');
      },
      pointermove: event => {
        if (!this.drag || event.pointerId !== this.drag.id) return;
        if (!(event.buttons & 1)) { this.end(); return; }
        const dx = event.clientX - this.drag.x, dy = event.clientY - this.drag.y;
        this.drag.x = event.clientX; this.drag.y = event.clientY;
        let pose;
        if (this.wristMode) {
          pose = [...this.pose];
          pose[3] = clamp(pose[3] - dy * .005, ...ranges[3]);
          this.callbacks.ik?.('Z · Yalnız bilek · Yukarı/aşağı sürükle');
        } else pose = this.moveTip(dx, dy, event.shiftKey);
        this.setPose(pose); this.callbacks.change(pose);
      },
      pointerup: event => { if (this.drag?.id === event.pointerId) this.end(); },
      pointercancel: () => this.end(), lostpointercapture: () => { if (this.drag) this.end(); },
      wheel: event => {
        event.preventDefault();
        if (this.drag) return;
        if (event.shiftKey) {
          const offset = this.camera.position.clone().sub(this.controls.target);
          const distance = Math.max(this.controls.minDistance, Math.min(this.controls.maxDistance, offset.length() * Math.exp(Math.max(-120, Math.min(120, event.deltaY)) * .002)));
          this.camera.position.copy(this.controls.target).add(offset.setLength(distance)); this.controls.update();
          return;
        }
        if (this.disabledJoints?.has(5) || !this.kinematics || !this.callbacks.canMove() || !Number.isFinite(event.deltaY) || event.deltaY === 0) return;
        if (!this.wheelActive) { this.wheelActive = true; this.callbacks.begin(); }
        clearTimeout(this.wheelTimer);
        const pixels = event.deltaY * (event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? this.host.clientHeight : 1);
        const pose = scrollJaw(this.pose, pixels);
        this.setPose(pose); this.callbacks.change(pose);
        this.wheelTimer = setTimeout(() => this.end(), 220);
      },
    };
    Object.entries(this.handlers).forEach(([name, handler]) => element.addEventListener(name, handler, name === 'wheel' ? {passive: false} : undefined));
  }
  end() {
    if (!this.drag && !this.wheelActive) return;
    const id = this.drag?.id; this.drag = null; this.wheelActive = false;
    clearTimeout(this.wheelTimer);
    this.renderer.domElement.classList.remove('dragging');
    if (id !== undefined && this.renderer.domElement.hasPointerCapture(id)) this.renderer.domElement.releasePointerCapture(id);
    this.callbacks.end();
  }
  dispose() {
    this.end(); cancelAnimationFrame(this.frame); this.resizeObserver.disconnect();
    Object.entries(this.handlers).forEach(([name, handler]) => this.renderer.domElement.removeEventListener(name, handler));
    if (typeof window !== 'undefined') Object.entries(this.keyHandlers).forEach(([name, handler]) => window.removeEventListener(name, handler));
    this.controls.dispose(); this.renderer.dispose();
    this.geometries?.forEach(geometry => geometry.dispose());
    this.scene.traverse(object => object.material?.dispose());
    this.renderer.domElement.remove();
  }
}
