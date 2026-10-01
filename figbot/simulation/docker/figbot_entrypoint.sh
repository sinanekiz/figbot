#!/usr/bin/env bash
set -e

source /opt/ros/jazzy/setup.bash
source /figbot_ws/install/setup.bash

exec "$@"
