param(
    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$PicoSdkPath = (Join-Path $env:LOCALAPPDATA "FIGBOT\toolchains\pico-sdk-2.3.0")
)

$ErrorActionPreference = "Stop"
$source = Join-Path $ProjectRoot "firmware\pico2_motion"
$build = Join-Path $source "build-pico2-sdk230"
$cmake = Get-ChildItem (Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages") -Recurse -Filter cmake.exe -ErrorAction SilentlyContinue |
    Where-Object FullName -Match "Kitware\.CMake" | Select-Object -First 1 -ExpandProperty FullName
$ninja = Get-ChildItem (Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages") -Recurse -Filter ninja.exe -ErrorAction SilentlyContinue |
    Where-Object FullName -Match "Ninja-build\.Ninja" | Select-Object -First 1 -ExpandProperty FullName
$armBin = Join-Path $env:USERPROFILE "scoop\apps\gcc-arm-none-eabi\current\bin"
$mingwBin = Join-Path $env:USERPROFILE "scoop\apps\mingw\current\bin"

foreach ($required in @($PicoSdkPath, $cmake, $ninja, $armBin, $mingwBin)) {
    if (-not $required -or -not (Test-Path -LiteralPath $required)) { throw "Firmware toolchain dependency missing: $required" }
}

$env:PICO_SDK_PATH = $PicoSdkPath
$env:Path = "$mingwBin;$armBin;$env:Path"
& $cmake -S $source -B $build -G Ninja "-DCMAKE_MAKE_PROGRAM=$ninja" -DPICO_BOARD=pico2
if ($LASTEXITCODE -ne 0) { throw "Pico 2 configure failed: $LASTEXITCODE" }
& $cmake --build $build --parallel
if ($LASTEXITCODE -ne 0) { throw "Pico 2 build failed: $LASTEXITCODE" }

$uf2 = Join-Path $build "figbot_pico2_motion.uf2"
if (-not (Test-Path -LiteralPath $uf2)) { throw "UF2 output missing: $uf2" }
$hash = Get-FileHash -LiteralPath $uf2 -Algorithm SHA256
Write-Output "$uf2`nSHA256=$($hash.Hash)"
