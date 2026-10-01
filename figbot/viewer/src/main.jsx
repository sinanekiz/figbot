import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import "./styles.css";
import rigData from "./generatedKinematics.json";

const benchParts = [
  ["arm", "Robot arm", ["ARM"], "arm.png"],
  ["gripper", "Gripper", ["GRP"], "gripper.png"],
  ["funnel", "Funnel", ["FUN"], "funnel.png"],
  ["camera", "Camera", ["VIS", "CAM"], "camera.png"],
  ["stand", "Stand", ["CHA", "FRAME"], "stand.png"],
  ["electronics", "Electronics", ["ELE"], "electronics.png"],
];
const roverParts = [
  ["arm", "RoArm-M3 arm", ["ARM"], "arm.png"],
  ["basket", "Collection basket", ["BASKET"], "funnel.png"],
  ["camera", "Ground camera", ["CAMERA"], "camera.png"],
  ["chassis", "Profile chassis", ["FRM", "DECK"], "stand.png"],
  ["runningGear", "Wheels & steering", ["TIRE", "RIM", "HUB", "KINGPIN", "KNUCKLE", "TIE-ROD", "STEER-ARM", "ACTUATOR"], "stand.png"],
  ["electronics", "Power & electronics", ["BATTERY", "ELECTRONICS"], "electronics.png"],
];
const partSets = { V0: benchParts, V1: benchParts, P0: roverParts };
const allPartKeys = [...new Set(Object.values(partSets).flat().map(([key]) => key))];
const jointDefaults = { J1: 0, J2: 0, J3: 0, J4: 0 };
const modelFiles = {
  V0: "/models/FIGBOT_V0_ASSEMBLY.glb",
  V1: "/models/FIGBOT_V1_ASSEMBLY.glb",
  P0: "/models/FIGBOT_P0_ROVER.glb",
};

function buildJointRig(root, pivots) {
  const meshes = [];
  root.traverse((obj) => obj.isMesh && meshes.push(obj));
  const named = (pattern) => meshes.filter((mesh) => pattern.test((mesh.name || "").toUpperCase()));
  const group = (name, xyz) => {
    const value = new THREE.Group();
    value.name = name;
    value.position.fromArray(xyz);
    root.add(value);
    return value;
  };
  const rig = {
    J1: group("RIG-J1", pivots.J1),
    J2: group("RIG-J2", pivots.J2),
    J3: group("RIG-J3", pivots.J3),
    J4: group("RIG-J4", pivots.J4),
  };
  // Build from the tool backwards. Object3D.attach preserves the generated
  // world transform while establishing the true serial kinematic hierarchy.
  named(/GRP|PUR-ACT-G1/).forEach((mesh) => rig.J4.attach(mesh));
  named(/ARM-005|ARM-006|PUR-MOT-J4/).forEach((mesh) => rig.J3.attach(mesh));
  rig.J3.attach(rig.J4);
  named(/ARM-003|ARM-004|PUR-MOT-J3/).forEach((mesh) => rig.J2.attach(mesh));
  rig.J2.attach(rig.J3);
  named(/ARM-002|PUR-MOT-J2/).forEach((mesh) => rig.J1.attach(mesh));
  rig.J1.attach(rig.J2);
  return rig;
}

function Icon({ type }) {
  const paths = {
    reset: (
      <>
        <circle cx="12" cy="12" r="7" />
        <path d="M12 2v4M12 18v4M2 12h4M18 12h4" />
      </>
    ),
    explode: (
      <>
        <path d="m12 2 8 4-8 4-8-4 8-4Z" />
        <path d="m4 11 8 4 8-4M4 16l8 4 8-4" />
      </>
    ),
    full: <path d="M8 3H3v5M16 3h5v5M8 21H3v-5M16 21h5v-5" />,
  };
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      {paths[type]}
    </svg>
  );
}

function Scene({ model, visibility, joints, exploded, onReady, onError }) {
  const mount = useRef(null);
  const engine = useRef(null);
  useEffect(() => {
    const host = mount.current;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color("#f7f9f8");
    scene.up.set(0, 0, 1);
    const camera = new THREE.PerspectiveCamera(
      35,
      host.clientWidth / host.clientHeight,
      1,
      5000,
    );
    camera.up.set(0, 0, 1);
    camera.position.set(1050, -1150, 880);
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    renderer.setSize(host.clientWidth, host.clientHeight);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    host.appendChild(renderer.domElement);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(0, 0, 230);
    controls.enableDamping = true;
    scene.add(new THREE.HemisphereLight(0xffffff, 0x435247, 2.2));
    const key = new THREE.DirectionalLight(0xffffff, 3);
    key.position.set(450, -500, 900);
    scene.add(key);
    const grid = new THREE.GridHelper(1500, 30, 0xb8c2bc, 0xdfe5e1);
    grid.rotation.x = Math.PI / 2;
    grid.position.z = -12;
    scene.add(grid);
    const state = {
      scene,
      camera,
      renderer,
      controls,
      root: null,
      initial: [1050, -1150, 880],
      targetHome: [0, 0, 230],
    };
    engine.current = state;
    const loader = new GLTFLoader();
    loader.load(
      modelFiles[model],
      async (gltf) => {
        state.root = gltf.scene;
        scene.add(gltf.scene);
        state.rig = model === "P0" ? null : buildJointRig(gltf.scene, rigData.pivots);
        gltf.scene.traverse((obj) => {
          if (obj.isMesh) {
            obj.userData.home = obj.position.clone();
            obj.material.side = THREE.DoubleSide;
          }
        });
        const box = new THREE.Box3().setFromObject(gltf.scene);
        const sphere = box.getBoundingSphere(new THREE.Sphere());
        const direction = new THREE.Vector3(1.05, -1.2, 0.78).normalize();
        const distance = Math.max(sphere.radius * 2.75, 1200);
        camera.position
          .copy(sphere.center)
          .add(direction.multiplyScalar(distance));
        controls.target.copy(sphere.center);
        state.initial = camera.position.toArray();
        state.targetHome = controls.target.toArray();
        controls.update();
        onReady();
      },
      undefined,
      (err) => onError(String(err)),
    );
    const resize = () => {
      camera.aspect = host.clientWidth / host.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(host.clientWidth, host.clientHeight);
    };
    window.addEventListener("resize", resize);
    let frame;
    const animate = () => {
      controls.update();
      renderer.render(scene, camera);
      frame = requestAnimationFrame(animate);
    };
    animate();
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("resize", resize);
      controls.dispose();
      renderer.dispose();
      host.removeChild(renderer.domElement);
    };
  }, [model]);

  useEffect(() => {
    const root = engine.current?.root;
    if (!root) return;
    root.traverse((obj) => {
      if (!obj.isMesh) return;
      const name = (obj.name || "").toUpperCase();
      for (const [key, , prefixes] of partSets[model])
        if (prefixes.some((prefix) => name.includes(prefix))) obj.visible = visibility[key];
    });
  }, [visibility, model]);

  useEffect(() => {
    const rig = engine.current?.rig;
    if (!rig) return;
    rig.J1.rotation.z = THREE.MathUtils.degToRad(joints.J1);
    rig.J2.rotation.y = THREE.MathUtils.degToRad(-joints.J2);
    rig.J3.rotation.y = THREE.MathUtils.degToRad(-joints.J3);
    rig.J4.rotation.y = THREE.MathUtils.degToRad(-joints.J4);
  }, [joints, model]);

  useEffect(() => {
    const root = engine.current?.root;
    if (!root) return;
    let i = 0;
    root.traverse((obj) => {
      if (!obj.isMesh) return;
      obj.position.copy(obj.userData.home || new THREE.Vector3());
      if (exploded && /ARM|GRP|FUN/.test(obj.name || "")) {
        obj.position.x += i * 12;
        obj.position.z += i * 18;
        i++;
      }
    });
  }, [exploded, model]);

  const reset = () => {
    const e = engine.current;
    if (!e) return;
    e.camera.position.fromArray(e.initial);
    e.controls.target.fromArray(e.targetHome);
    e.controls.update();
  };
  useEffect(() => {
    mount.current.resetView = reset;
  }, []);
  return <div className="scene" ref={mount} data-testid="viewport" />;
}

function App() {
  const [model, setModel] = useState("V0");
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState("");
  const [visibility, setVisibility] = useState(
    Object.fromEntries(allPartKeys.map((key) => [key, true])),
  );
  const [joints, setJoints] = useState(jointDefaults);
  const [exploded, setExploded] = useState(false);
  const sceneWrap = useRef(null);
  useEffect(() => {
    document.title = `FIGBOT / ${model} Digital Twin`;
  }, [model]);
  const reset = () => {
    setJoints(jointDefaults);
    setExploded(false);
    sceneWrap.current?.querySelector(".scene")?.resetView?.();
  };
  return (
    <main className="app">
      <header>
        <h1>FIGBOT / {model} DIGITAL TWIN</h1>
        <div className="top-actions">
          <div className="segmented" aria-label="Model version">
            {Object.keys(modelFiles).map((name) => (
              <button
                key={name}
                className={model === name ? "active" : ""}
                onClick={() => {
                  setLoaded(false);
                  setModel(name);
                }}
              >
                {name}
              </button>
            ))}
          </div>
          <button onClick={reset}>
            <Icon type="reset" />
            Reset View
          </button>
          <button
            className={exploded ? "selected" : ""}
            onClick={() => setExploded((v) => !v)}
          >
            <Icon type="explode" />
            Exploded
          </button>
          <button
            disabled={model === "P0"}
            onClick={() => setJoints({ J1: 25, J2: 20, J3: -30, J4: 15 })}
            title="Apply a visible offset pose to verify the serial joint hierarchy"
          >
            Test Pose
          </button>
          <button
            className="icon-button"
            aria-label="Fullscreen"
            onClick={() => document.documentElement.requestFullscreen?.()}
          >
            <Icon type="full" />
          </button>
        </div>
      </header>
      <section className="workspace">
        <aside className="parts-panel">
          <h2>PARTS</h2>
          {partSets[model].map(([key, label, , asset]) => (
            <label className="part-row" key={key}>
              <img src={`/thumbnails/${asset}`} alt="" />
              <span>{label}</span>
              <input
                type="checkbox"
                checked={visibility[key]}
                onChange={(e) =>
                  setVisibility((v) => ({ ...v, [key]: e.target.checked }))
                }
              />
              <i />
            </label>
          ))}
        </aside>
        <div className="viewport-wrap" ref={sceneWrap}>
          <Scene
            model={model}
            visibility={visibility}
            joints={joints}
            exploded={exploded}
            onReady={() => {
              setLoaded(true);
              setError("");
            }}
            onError={setError}
          />
          {!loaded && !error && (
            <div className="loading">Loading engineering model…</div>
          )}
          {error && (
            <div className="loading error">Model load failed: {error}</div>
          )}
          <div className="axis">
            <b>Z</b>
            <span>Y</span>
            <em>X</em>
          </div>
        </div>
        <aside className="joints">
          <h2>JOINT CONTROL</h2>
          {model === "P0" && (
            <p className="model-note">
              P0 is the front-steer packaging model. Its Ackermann joints are controlled in the ROS/URDF simulation.
            </p>
          )}
          {Object.keys(jointDefaults).map((key, i) => (
            <div className="joint" key={key}>
              <div>
                <label>
                  {key} {["BASE OFFSET", "SHOULDER OFFSET", "ELBOW OFFSET", "TOOL OFFSET"][i]}
                </label>
                <output>{joints[key].toFixed(1)}°</output>
              </div>
              <input
                type="range"
                disabled={model === "P0"}
                min={key === "J1" ? -115 : -100}
                max={key === "J3" ? 135 : 100}
                step="1"
                value={joints[key]}
                onChange={(e) =>
                  setJoints((v) => ({ ...v, [key]: Number(e.target.value) }))
                }
              />
              <div className="scale">
                <span>-</span>
                <span>0°</span>
                <span>+</span>
              </div>
            </div>
          ))}
        </aside>
      </section>
      <footer>
        <strong>PROTOTYPE — NOT PRODUCTION VALIDATED</strong>
        <span>Model: {modelFiles[model].split("/").at(-1)}</span>
      </footer>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
