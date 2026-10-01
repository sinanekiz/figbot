$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
function Move-ProjectItem([string]$Source, [string]$Destination) {
    $fromPath = [IO.Path]::GetFullPath((Join-Path $projectRoot $Source))
    $toPath = [IO.Path]::GetFullPath((Join-Path $projectRoot $Destination))
    foreach ($checkedPath in @($fromPath, $toPath)) {
        if (-not $checkedPath.StartsWith($projectRoot + [IO.Path]::DirectorySeparatorChar)) { throw 'Path outside project' }
    }
    if (-not (Test-Path -LiteralPath $fromPath)) { throw "Missing source: $Source" }
    if (Test-Path -LiteralPath $toPath) { throw "Destination already exists: $Destination" }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $toPath) | Out-Null
    Move-Item -LiteralPath $fromPath -Destination $toPath
    Write-Output "$Source -> $Destination"
}
Move-ProjectItem 'GUNCEL' 'reports/project_organization/INCOMPLETE_COPY'
Move-ProjectItem 'releases/LINKA_L1_3_TABLALAR' 'GUNCEL/BASKI'
Move-ProjectItem 'cad/prototype_arm/linka_v1' 'GUNCEL/CAD'
Move-ProjectItem 'purchasing/LINKA_L1_20260914' 'GUNCEL/ALISVERIS/VERI'
Move-ProjectItem 'output/pdf/FIGBOT_HIRDAVATCI_ALISVERIS_LISTESI_A4.pdf' 'GUNCEL/ALISVERIS/FIGBOT_HIRDAVATCI_ALISVERIS_LISTESI_A4.pdf'
Move-ProjectItem 'releases/FIGBOT-Kontrol-HC05-v0.11-debug.apk' 'GUNCEL/YAZILIM/FIGBOT_MOTOR_KONTROL.apk'
Move-ProjectItem 'releases/FIGBOT-Kuru-Incir-Tarayici-v0.6-debug.apk' 'GUNCEL/YAZILIM/FIGBOT_INCIR_TARAYICI.apk'
Move-ProjectItem 'releases/FIGBOT-UNO-HC05-V5-calibration.ino.hex' 'GUNCEL/YAZILIM/UNO_HC05.hex'
Move-ProjectItem 'releases/FIGBOT-UNO-USB-V5-calibration.ino.hex' 'GUNCEL/YAZILIM/UNO_USB.hex'
Move-ProjectItem 'viewer/public/models/linka-v1' 'viewer/public/models/guncel'
Copy-Item -LiteralPath (Join-Path $projectRoot 'viewer/linka-v1.html') -Destination (Join-Path $projectRoot 'viewer/kol.html')
