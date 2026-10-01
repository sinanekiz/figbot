# External Tool Setup

Installed and verified on 2026-08-20:

- **FreeCAD 1.1.3** is installed for the current Windows user at `%LOCALAPPDATA%\Programs\FreeCAD 1.1`. Run `scripts\open_in_freecad.py` to open V0, or `scripts\freecad_validate.ps1` to import both STEP assemblies and regenerate their native FCStd files.
- **Docker Desktop / Engine 29.6.1** supplies the Linux runtime. A separate Ubuntu application or WSL distribution is not required.
- **ROS 2 Jazzy + Gazebo Harmonic** are installed in Docker image `figbot/ros2-gazebo:jazzy-harmonic`. Gazebo Sim reports 8.11.0.

PowerShell commands:

```powershell
.\scripts\figbot_docker.ps1 build
.\scripts\figbot_docker.ps1 validate
.\scripts\figbot_docker.ps1 shell
.\scripts\figbot_docker.ps1 gazebo-headless
```

The validated Docker path is headless. It runs the physics server and ROS bridge without a Windows display server. Gazebo GUI display from Docker needs a separately configured X/Wayland endpoint; that is not required for the automated simulation gate.
