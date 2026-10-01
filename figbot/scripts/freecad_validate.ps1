$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$freecadCmd = Join-Path $env:LOCALAPPDATA "Programs\FreeCAD 1.1\bin\freecadcmd.exe"
$validator = Join-Path $PSScriptRoot "validate_freecad.py"

if (-not (Test-Path -LiteralPath $freecadCmd)) {
    throw "FreeCADCmd bulunamadı: $freecadCmd"
}

$python = "p=r'$validator'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'), {'__file__': p, '__name__': '__main__'})"
$python | & $freecadCmd -c

if ($LASTEXITCODE -ne 0) {
    throw "FreeCAD doğrulaması exit code $LASTEXITCODE ile başarısız oldu."
}
