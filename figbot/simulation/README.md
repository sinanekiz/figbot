# ROS 2 and Gazebo simulation

The supported Windows path uses Docker Desktop rather than a separate Ubuntu installation.

- Base: Ubuntu 24.04 / ROS 2 Jazzy
- Simulator: Gazebo Harmonic (Gazebo Sim 8.11.0 at verification time)
- ROS bridge: `ros_gz_bridge`
- Controls: `ros2_control`, joint-state broadcaster, and joint-trajectory controller
- Project package: `simulation/ros2/figbot_description`
- World: `simulation/worlds/figbot_v0.world.sdf`

From the repository root in PowerShell:

```powershell
.\scripts\figbot_docker.ps1 build
.\scripts\figbot_docker.ps1 validate
```

`validate` expands and checks both the V0 arm and P0 front-steer rover URDF trees, locates the installed ROS package, reports the Gazebo version, and runs the V0 world headlessly for 12 seconds. A timeout exit of 124 is expected and treated as success because the physics server is intentionally terminated after the smoke-test window.

For an interactive shell:

```powershell
.\scripts\figbot_docker.ps1 shell
```

The image contains Gazebo GUI libraries, but Docker Desktop does not expose a Windows display endpoint by default. The checked path is the headless server; configure an X/Wayland endpoint before attempting a GUI client.
