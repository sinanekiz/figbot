param(
    [ValidateSet("build", "validate", "shell", "gazebo-headless")]
    [string]$Action = "validate"
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$composeFile = Join-Path $projectRoot "simulation\docker\compose.yaml"

switch ($Action) {
    "build" {
        docker compose --file $composeFile build
    }
    "validate" {
        docker compose --file $composeFile run --rm figbot bash -lc @'
set -e
xacro /figbot_ws/src/figbot_description/urdf/figbot_v0.urdf.xacro > /tmp/figbot_v0.urdf
check_urdf /tmp/figbot_v0.urdf
xacro /figbot_ws/src/figbot_description/urdf/figbot_p0_rover.urdf.xacro > /tmp/figbot_p0_rover.urdf
check_urdf /tmp/figbot_p0_rover.urdf
ros2 pkg prefix figbot_description
gz sim --versions
timeout 12s gz sim -s -r /figbot/worlds/figbot_v0.world.sdf || test $? -eq 124
'@
    }
    "shell" {
        docker compose --file $composeFile run --rm figbot bash
    }
    "gazebo-headless" {
        docker compose --file $composeFile run --rm figbot `
            gz sim -s -r /figbot/worlds/figbot_v0.world.sdf
    }
}

if ($LASTEXITCODE -ne 0) {
    throw "FIGBOT Docker action '$Action' failed with exit code $LASTEXITCODE."
}
