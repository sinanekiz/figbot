#!/usr/bin/env bash
set -euo pipefail

repo_dir="${1:-/opt/figbot}"
if [[ ! -f "$repo_dir/requirements.txt" ]]; then
  echo "FIGBOT repository not found at $repo_dir" >&2
  exit 2
fi

sudo apt-get update
sudo apt-get install -y python3-venv python3-picamera2 python3-opencv python3-numpy git cmake ninja-build
python3 -m venv --system-site-packages "$repo_dir/.venv-pi5"
"$repo_dir/.venv-pi5/bin/python" -m pip install --upgrade pip
"$repo_dir/.venv-pi5/bin/python" -m pip install -r "$repo_dir/requirements.txt"
"$repo_dir/.venv-pi5/bin/python" -m pytest -q "$repo_dir/tests" "$repo_dir/software" "$repo_dir/ai"

echo "Provisioning complete. Physical commissioning is still required."
