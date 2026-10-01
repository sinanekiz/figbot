$ErrorActionPreference = 'Stop'
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    uv sync --frozen --extra test
    if ($LASTEXITCODE -ne 0) { throw 'Environment installation failed' }
    & .venv/Scripts/python.exe -m figbot_lab.cli download --model all --reference
    if ($LASTEXITCODE -ne 0) { throw 'Model download failed' }
    & .venv/Scripts/python.exe -m figbot_lab.cli doctor
    if ($LASTEXITCODE -ne 0) { throw 'Environment check failed' }
} finally {
    Pop-Location
}
