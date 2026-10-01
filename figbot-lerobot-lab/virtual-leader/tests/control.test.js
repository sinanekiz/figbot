import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import * as THREE from 'three';
import {STLLoader} from 'three/addons/loaders/STLLoader.js';
import {scrollJaw, initialPose, ranges} from '../src/control.js';
import {KinematicArm, fingerReference, screenDisplacement} from '../src/Kinematics.js';
import {RobotScene, createViewControls} from '../src/RobotScene.js';

const model = JSON.parse(fs.readFileSync(new URL('../public/robot/model.json', import.meta.url)));
const bytes = fs.readFileSync(new URL('../public/robot/wrist_roll_follower_so101_v1.stl', import.meta.url));
const geometry = new STLLoader().parse(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength));
const reference = fingerReference(model, geometry);
const arm = () => new KinematicArm(model, reference);

test('wheel down opens, up closes, with bounded steps and unchanged arm/source', () => {
  const source = [...initialPose], down = scrollJaw(source, 100), up = scrollJaw(source, -100);
  assert.ok(down[5] > source[5]); assert.ok(up[5] < source[5]);
  assert.deepEqual(down.slice(0, 5), source.slice(0, 5)); assert.deepEqual(source, initialPose);
  assert.ok(scrollJaw(source, 10000)[5] - source[5] <= .097);
  assert.equal(scrollJaw([0, 0, 0, 0, 0, ranges[5][1]], 100)[5], ranges[5][1]);
});

test('fixed tip reference remains independent of jaw opening', () => {
  const k = arm(), first = k.forward(initialPose), changed = [...initialPose]; changed[5] += .5;
  assert.ok(k.forward(changed).position.distanceTo(first.position) < 1e-10);
  assert.ok(first.position.toArray().every(Number.isFinite));
});

test('nearby tip target coordinates several joints and preserves jaw opening', () => {
  const k = arm(), start = k.forward(initialPose);
  const target = start.position.clone().add(new THREE.Vector3(.007, .008, -.005));
  const source = [...initialPose], result = k.solve(source, target, start.orientation);
  assert.ok(result.error < start.position.distanceTo(target) * .35, 'error ' + result.error);
  assert.ok(result.pose.slice(0, 5).filter((v, i) => Math.abs(v - source[i]) > .001).length >= 3);
  assert.equal(result.pose[5], source[5]); assert.deepEqual(source, initialPose);
});

test('unreachable target remains finite, within model limits and bounded from previous pose', () => {
  const k = arm(), start = k.forward(initialPose), result = k.solve(initialPose, new THREE.Vector3(20, 20, 20), start.orientation);
  for (let i = 0; i < 5; i++) {
    assert.ok(Number.isFinite(result.pose[i]));
    assert.ok(result.pose[i] >= k.limits[i][0] && result.pose[i] <= k.limits[i][1]);
    assert.ok(Math.abs(result.pose[i] - initialPose[i]) <= .120001);
  }
  assert.throws(() => k.solve(initialPose, new THREE.Vector3(NaN, 0, 0), start.orientation));
});

test('screen motion follows camera axes; Shift changes vertical motion to depth', () => {
  const camera = new THREE.PerspectiveCamera(36, 1, .001, 6); camera.position.set(.5, .4, .5); camera.lookAt(0, .15, 0);
  const point = new THREE.Vector3(0, .15, 0), up = new THREE.Vector3(0, 1, 0).applyQuaternion(camera.quaternion);
  const forward = new THREE.Vector3(0, 0, -1).applyQuaternion(camera.quaternion);
  assert.ok(screenDisplacement(camera, point, 800, 0, -20).dot(up) > 0);
  assert.ok(screenDisplacement(camera, point, 800, 0, -20, true).dot(forward) > 0);
  assert.ok(Math.abs(screenDisplacement(camera, point, 800, 0, -20, true).dot(up)) < 1e-10);
});

function fakeScene() {
  const listeners = {}, captured = new Set(), counts = {began: 0, ended: 0, changed: 0};
  const element = {addEventListener: (name, fn) => listeners[name] = fn, focus() {},
    classList: {add() {}, remove() {}}, setPointerCapture: id => captured.add(id),
    hasPointerCapture: id => captured.has(id), releasePointerCapture: id => captured.delete(id)};
  const scene = Object.create(RobotScene.prototype), camera = new THREE.PerspectiveCamera(36, 1, .001, 6);
  camera.position.set(.5, .4, .5); camera.lookAt(0, .15, 0);
  Object.assign(scene, {renderer: {domElement: element}, pose: [...initialPose], kinematics: arm(), camera, host: {clientHeight: 800},
    callbacks: {canMove: () => true, begin: () => counts.began++, end: () => counts.ended++, change: () => counts.changed++},
    setPose(value) { this.pose = value; }});
  scene.bind(); return {scene, listeners, counts};
}

test('left pointer gesture moves multiple joints and freezes on release/capture loss', () => {
  const {scene, listeners, counts} = fakeScene();
  listeners.pointerdown({button: 0, pointerId: 1, clientX: 50, clientY: 50, preventDefault() {}});
  listeners.pointermove({buttons: 1, pointerId: 1, clientX: 60, clientY: 35, shiftKey: false});
  assert.ok(scene.pose.slice(0, 5).filter((v, i) => Math.abs(v - initialPose[i]) > .001).length >= 2);
  assert.equal(scene.pose[5], initialPose[5]);
  listeners.pointerup({pointerId: 1}); const released = [...scene.pose];
  listeners.pointermove({buttons: 0, pointerId: 1, clientX: 80, clientY: 15}); listeners.lostpointercapture();
  assert.deepEqual(scene.pose, released); assert.equal(counts.ended, 1); assert.equal(counts.changed, 1);
});

test('right button never starts a motor gesture or changes arm/jaw', () => {
  const {scene, listeners, counts} = fakeScene();
  listeners.pointerdown({button: 2, pointerId: 1, clientX: 50, clientY: 50, preventDefault() {}});
  listeners.pointermove({buttons: 2, pointerId: 1, clientX: 90, clientY: 90});
  assert.deepEqual(scene.pose, initialPose); assert.equal(counts.began, 0); assert.equal(counts.changed, 0);
});

test('Z with left drag changes only wrist flex; release holds that pose', () => {
  const {scene, listeners, counts} = fakeScene();
  scene.keyHandlers.keydown({code: 'KeyZ', target: {tagName: 'CANVAS'}});
  listeners.pointerdown({button: 0, pointerId: 1, clientX: 50, clientY: 50, preventDefault() {}});
  listeners.pointermove({buttons: 1, pointerId: 1, clientX: 150, clientY: 30, shiftKey: true});
  assert.ok(scene.pose[3] > initialPose[3]);
  for (const i of [0, 1, 2, 4, 5]) assert.equal(scene.pose[i], initialPose[i]);
  listeners.pointermove({buttons: 1, pointerId: 1, clientX: 150, clientY: -10000});
  assert.equal(scene.pose[3], ranges[3][1]);
  listeners.pointerup({pointerId: 1}); const released = [...scene.pose];
  listeners.pointermove({buttons: 1, pointerId: 1, clientX: 200, clientY: 300});
  assert.deepEqual(scene.pose, released); assert.equal(counts.ended, 1);
});

test('releasing Z during drag restores coordinated motion from the new orientation', () => {
  const {scene, listeners} = fakeScene();
  scene.keyHandlers.keydown({key: 'z'});
  listeners.pointerdown({button: 0, pointerId: 1, clientX: 50, clientY: 50, preventDefault() {}});
  listeners.pointermove({buttons: 1, pointerId: 1, clientX: 50, clientY: 30});
  const wristPose = [...scene.pose];
  scene.keyHandlers.keyup({code: 'KeyZ'});
  assert.ok(scene.drag.orientation.angleTo(scene.kinematics.forward(wristPose).orientation) < 1e-8);
  listeners.pointermove({buttons: 1, pointerId: 1, clientX: 65, clientY: 20});
  assert.ok([0, 1, 2, 4].some(i => Math.abs(scene.pose[i] - wristPose[i]) > .001));
  assert.equal(scene.pose[5], wristPose[5]); scene.end();
});

test('Z typing in a field is ignored and focus loss releases wrist mode and gesture', () => {
  const {scene, listeners, counts} = fakeScene();
  scene.keyHandlers.keydown({code: 'KeyZ', target: {tagName: 'INPUT'}});
  assert.equal(scene.wristMode, false);
  scene.keyHandlers.keydown({code: 'KeyZ', target: {isContentEditable: true}});
  assert.equal(scene.wristMode, false);
  scene.keyHandlers.keydown({code: 'KeyZ'});
  listeners.pointerdown({button: 2, pointerId: 1, clientX: 50, clientY: 50});
  assert.equal(counts.began, 0);
  listeners.pointerdown({button: 0, pointerId: 1, clientX: 50, clientY: 50, preventDefault() {}});
  scene.keyHandlers.blur();
  assert.equal(scene.wristMode, false); assert.equal(scene.drag, null); assert.equal(counts.ended, 1);
});

test('real OrbitControls rotates view with right drag and leaves wheel zoom disabled', () => {
  class Target {
    constructor() { this.handlers = new Map(); this.style = {}; this.clientHeight = this.clientWidth = 800; }
    addEventListener(name, fn) { if (!this.handlers.has(name)) this.handlers.set(name, new Set()); this.handlers.get(name).add(fn); }
    removeEventListener(name, fn) { this.handlers.get(name)?.delete(fn); }
    emit(name, event) { for (const fn of this.handlers.get(name) || []) fn(event); }
    setPointerCapture() {} releasePointerCapture() {} getRootNode() { return this.ownerDocument; }
  }
  const element = new Target(); element.ownerDocument = new Target();
  const camera = new THREE.PerspectiveCamera(36, 1, .001, 6); camera.position.set(.5, .4, .5);
  const controls = createViewControls(camera, element), start = camera.position.clone();
  const event = {pointerId: 1, pointerType: 'mouse', button: 2, clientX: 100, clientY: 100, preventDefault() {}};
  element.emit('pointerdown', event);
  element.ownerDocument.emit('pointermove', {...event, clientX: 180, clientY: 140});
  element.ownerDocument.emit('pointerup', event);
  assert.ok(camera.position.distanceTo(start) > .01);
  const afterRotation = camera.position.clone();
  element.emit('wheel', {deltaY: 100, preventDefault() {}});
  assert.ok(camera.position.distanceTo(afterRotation) < 1e-10);
  controls.dispose();
});

test('wheel event moves only jaw then ends the gesture; stopped scene ignores wheel', async () => {
  const {scene, listeners, counts} = fakeScene();
  listeners.wheel({deltaY: 100, deltaMode: 0, shiftKey: false, preventDefault() {}});
  assert.ok(scene.pose[5] > initialPose[5]); assert.deepEqual(scene.pose.slice(0, 5), initialPose.slice(0, 5));
  assert.equal(counts.began, 1);
  await new Promise(resolve => setTimeout(resolve, 250));
  assert.equal(counts.ended, 1); assert.equal(scene.wheelActive, false);
  const released = [...scene.pose]; scene.callbacks.canMove = () => false;
  listeners.wheel({deltaY: 100, deltaMode: 0, shiftKey: false, preventDefault() {}});
  assert.deepEqual(scene.pose, released);
});

test('absent gripper ignores wheel without disabling coordinated arm or Z wrist', () => {
  const {scene, listeners, counts} = fakeScene();
  scene.setDisabledJoints([5]);
  listeners.wheel({deltaY: 100, deltaMode: 0, shiftKey: false, preventDefault() {}});
  assert.deepEqual(scene.pose, initialPose); assert.equal(counts.began, 0);
  scene.keyHandlers.keydown({code: 'KeyZ'});
  listeners.pointerdown({button: 0, pointerId: 1, clientX: 50, clientY: 50, preventDefault() {}});
  listeners.pointermove({buttons: 1, pointerId: 1, clientX: 50, clientY: 30});
  assert.notEqual(scene.pose[3], initialPose[3]); assert.equal(scene.pose[5], initialPose[5]);
  scene.end();
});
