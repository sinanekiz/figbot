param(
    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot)
)

$manifest = Join-Path $ProjectRoot "manufacturing\PARTGO_RFQ_MANIFEST.csv"
if (-not (Test-Path -LiteralPath $manifest)) { throw "RFQ manifest missing: $manifest" }
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$packRoot = Join-Path $ProjectRoot "releases\PARTGO-RFQ-$stamp"
New-Item -ItemType Directory -Path $packRoot | Out-Null

$rows = Import-Csv -LiteralPath $manifest
foreach ($row in $rows) {
    if ($row.release_status -like "BLOCKED*") { continue }
    $partDir = Join-Path $packRoot $row.part_number
    New-Item -ItemType Directory -Path $partDir | Out-Null
    foreach ($relative in @($row.upload_file, $row.companion_drawing)) {
        $source = Join-Path $ProjectRoot $relative
        if (-not (Test-Path -LiteralPath $source)) { throw "RFQ file missing: $source" }
        Copy-Item -LiteralPath $source -Destination $partDir
    }
}
Copy-Item -LiteralPath $manifest -Destination $packRoot
Copy-Item -LiteralPath (Join-Path $ProjectRoot "manufacturing\INTERFACE_CONTROL.csv") -Destination $packRoot
$zip = "$packRoot.zip"
Compress-Archive -LiteralPath $packRoot -DestinationPath $zip
Write-Output $zip
