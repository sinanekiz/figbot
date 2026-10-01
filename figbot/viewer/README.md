# FIGBOT local 3D viewer

Active FORMA V6: open `http://127.0.0.1:5173/forma-v6.html` after starting Vite.
The whole arm, exposed J1 base, rover pickup and release load from current V6 GLB exports.
`python -m cad.prototype_arm.export_forma_v6` refreshes those four assets automatically.
Motor visibility and transparent plastic are inspection aids; cable geometry and physical mounting are not validated.

The viewer loads generated named-node GLB assemblies and provides orbit, pan, zoom, subsystem visibility, V0/V1/P0 switching, exploded view, fullscreen, and V0/V1 J1-J4 engineering-preview controls. P0 steering motion is represented in the ROS/URDF model; the web P0 tab is the controlled static packaging review.

```powershell
cd viewer
npm install
npm run dev
```

Open the printed local URL. Rebuild models with `..\.venv\Scripts\python ..\scripts\build_all.py --skip-tests` after CAD changes.

Joint controls are a visual review aid, not a physics or collision simulation. Use the Python kinematic tests and Gazebo package for motion claims.

Visual design reference: `../references/viewer_ui_concept.png` (concept only, not a dimension source).
