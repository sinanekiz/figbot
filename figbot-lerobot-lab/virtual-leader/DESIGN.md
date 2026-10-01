# Sanal sürücü arayüzü

Concept: `design/concept.png`, 1586 × 992. Default mode authorizes implementation without a separate design approval.

White header and inspector, gray viewport, blue SO101, emerald selection, red stop.
Segoe UI; title 26px/700, section 19px/700, controls 14px, notes 12px.
Header, flexible 3D viewport, 340px inspector, bottom status; 20px gutters.
Five joint rows plus jaw; port/read/start; recording. No decorative dashboard tiles.
Real model replaces the concept's inaccurate illustrative arm, using unmodified source
mesh geometry and MuJoCo transformations. Software colors may differ from printed parts.
Required functional additions: calibration status/help, real feedback, disconnect,
simulation-only reset, visible error messages and recording location. No movement on page load.
Mouse (user's corrected request): left drag translates the tip through coupled IK;
Shift + left changes depth; wheel changes jaw opening; right rotates the view;
Shift + wheel zooms. Add a green tip handle and update the existing mouse hints.
Real control requires fresh measured pose and a physically verified profile.
