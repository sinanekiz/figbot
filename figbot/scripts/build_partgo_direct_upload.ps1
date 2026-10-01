param(
    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path -LiteralPath $ProjectRoot).Path
$releaseRoot = Join-Path $root "releases"
if (-not (Test-Path -LiteralPath $releaseRoot)) { New-Item -ItemType Directory -Path $releaseRoot | Out-Null }
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$output = Join-Path $releaseRoot "PARTGO-DIRECT-UPLOAD-$stamp"
New-Item -ItemType Directory -Path $output | Out-Null

$items = @(
    # CNC STEP: one solid part per direct-upload file.
    @{Part="ARM-001"; Qty=1; Material="EN AW-6082-T6"; Process="CNC milling"; Group="01_CNC_STEP_DOGRUDAN_YUKLE"; Source="cad\arm\ARM-001\ARM-001.step"; Target="ARM-001_QTY1_6082-T6_CNC.step"; Status="RFQ_ONLY_FIRST_ARTICLE"},
    @{Part="ARM-002"; Qty=1; Material="EN AW-6082-T6"; Process="CNC milling/fabrication"; Group="01_CNC_STEP_DOGRUDAN_YUKLE"; Source="cad\arm\ARM-002\ARM-002.step"; Target="ARM-002_QTY1_6082-T6_CNC.step"; Status="RFQ_ONLY_FIRST_ARTICLE"},
    @{Part="ARM-003"; Qty=1; Material="EN AW-6060-T66 or 6082-T6 40x30x2 tube"; Process="Saw and jig drill"; Group="01_CNC_STEP_DOGRUDAN_YUKLE"; Source="cad\arm\ARM-003\ARM-003.step"; Target="ARM-003_QTY1_40x30x2_TUBE.step"; Status="RFQ_ONLY_MANUAL_PROCESS_REVIEW"},
    @{Part="ARM-004"; Qty=1; Material="EN AW-6082-T6"; Process="CNC milling"; Group="01_CNC_STEP_DOGRUDAN_YUKLE"; Source="cad\arm\ARM-004\ARM-004.step"; Target="ARM-004_QTY1_6082-T6_CNC.step"; Status="RFQ_ONLY_FIRST_ARTICLE"},
    @{Part="ARM-005"; Qty=1; Material="EN AW-6060-T66 or 6082-T6 40x30x2 tube"; Process="Saw and jig drill"; Group="01_CNC_STEP_DOGRUDAN_YUKLE"; Source="cad\arm\ARM-005\ARM-005.step"; Target="ARM-005_QTY1_40x30x2_TUBE.step"; Status="RFQ_ONLY_MANUAL_PROCESS_REVIEW"},
    @{Part="ARM-006"; Qty=1; Material="EN AW-6082-T6"; Process="CNC milling"; Group="01_CNC_STEP_DOGRUDAN_YUKLE"; Source="cad\arm\ARM-006\ARM-006.step"; Target="ARM-006_QTY1_6082-T6_CNC.step"; Status="RFQ_ONLY_FIRST_ARTICLE"},
    @{Part="ARM-007"; Qty=2; Material="C45 or 42CrMo4+QT"; Process="CNC turning"; Group="01_CNC_STEP_DOGRUDAN_YUKLE"; Source="cad\arm\ARM-007\ARM-007.step"; Target="ARM-007_QTY2_C45_CNC-TURN.step"; Status="QUOTE_ONLY_NOT_RELEASED"},
    @{Part="ARM-008"; Qty=2; Material="C45 or 42CrMo4+QT"; Process="CNC turning"; Group="01_CNC_STEP_DOGRUDAN_YUKLE"; Source="cad\arm\ARM-008\ARM-008.step"; Target="ARM-008_QTY2_C45_CNC-TURN.step"; Status="QUOTE_ONLY_NOT_RELEASED"},

    # Printable prototype/tooling STL files.
    @{Part="GRP-001"; Qty=1; Material="PA12 SLS preferred"; Process="3D print"; Group="02A_3D_BASKI_STL_DOGRUDAN_YUKLE"; Source="cad\gripper\GRP-001\GRP-001.stl"; Target="GRP-001_QTY1_PA12-SLS.stl"; Status="RFQ_ONLY_PHYSICAL_FIT"},
    @{Part="GRP-004"; Qty=1; Material="PA12 carrier prototype"; Process="3D print"; Group="02A_3D_BASKI_STL_DOGRUDAN_YUKLE"; Source="cad\gripper\GRP-004\GRP-004.stl"; Target="GRP-004_QTY1_PA12-CARRIER.stl"; Status="RFQ_ONLY_PHYSICAL_FIT"},
    @{Part="GRP-005"; Qty=1; Material="Resin or PETG tooling"; Process="3D print mold"; Group="02A_3D_BASKI_STL_DOGRUDAN_YUKLE"; Source="cad\gripper\GRP-005\GRP-005.stl"; Target="GRP-005_QTY1_MOLD.stl"; Status="RFQ_ONLY_TOOLING"},
    @{Part="GRP-006"; Qty=1; Material="Resin or PETG tooling"; Process="3D print mold"; Group="02A_3D_BASKI_STL_DOGRUDAN_YUKLE"; Source="cad\gripper\GRP-006\GRP-006.stl"; Target="GRP-006_QTY1_MOLD.stl"; Status="RFQ_ONLY_TOOLING"},
    @{Part="GRP-007"; Qty=1; Material="Resin or PETG tooling"; Process="3D print mold"; Group="02A_3D_BASKI_STL_DOGRUDAN_YUKLE"; Source="cad\gripper\GRP-007\GRP-007.stl"; Target="GRP-007_QTY1_MOLD.stl"; Status="RFQ_ONLY_TOOLING"},
    @{Part="FUN-001"; Qty=1; Material="PETG prototype"; Process="3D print"; Group="02A_3D_BASKI_STL_DOGRUDAN_YUKLE"; Source="cad\funnel\FUN-001\FUN-001.stl"; Target="FUN-001_QTY1_PETG.stl"; Status="RFQ_ONLY_DROP_TEST"},
    @{Part="FUN-003"; Qty=1; Material="TPU prototype"; Process="3D print"; Group="02A_3D_BASKI_STL_DOGRUDAN_YUKLE"; Source="cad\funnel\FUN-003\FUN-003.stl"; Target="FUN-003_QTY1_TPU.stl"; Status="RFQ_ONLY_DROP_TEST"},

    # Geometry references: not final printable material.
    @{Part="GRP-002"; Qty=2; Material="Food-contact silicone candidate"; Process="Silicone casting"; Group="02B_GEOMETRI_REFERANSI_MALZEME_FINAL_DEGIL"; Source="cad\gripper\GRP-002\GRP-002.stl"; Target="GRP-002_QTY2_SILICONE-GEOMETRY.stl"; Status="GEOMETRY_ONLY_NOT_FINAL_MATERIAL"},
    @{Part="GRP-003"; Qty=2; Material="Food-contact silicone candidate"; Process="Silicone casting"; Group="02B_GEOMETRI_REFERANSI_MALZEME_FINAL_DEGIL"; Source="cad\gripper\GRP-003\GRP-003.stl"; Target="GRP-003_QTY2_SILICONE-GEOMETRY.stl"; Status="GEOMETRY_ONLY_NOT_FINAL_MATERIAL"},
    @{Part="FUN-002"; Qty=1; Material="Food-contact silicone candidate"; Process="Silicone casting/forming"; Group="02B_GEOMETRI_REFERANSI_MALZEME_FINAL_DEGIL"; Source="cad\funnel\FUN-002\FUN-002.stl"; Target="FUN-002_QTY1_SILICONE-LINER-GEOMETRY.stl"; Status="GEOMETRY_ONLY_NOT_FINAL_MATERIAL"},

    # Sheet files accepted for quote; still subject to release notes.
    @{Part="ELE-001"; Qty=1; Material="EN AW-5754 H22 3 mm"; Process="Sheet cutting"; Group="03_SAC_DXF_TEKLIF"; Source="cad\test_stand\ELE-001\ELE-001.dxf"; Target="ELE-001_QTY1_5754-H22_3MM.dxf"; Status="QUOTE_ONLY_NOT_RELEASED_DEVICE_HOLES"},

    # Reference files; intentionally not sent to instant single-part pricing.
    @{Part="VIS-001"; Qty=1; Material="30-series extrusion plus EN AW-5754 bracket"; Process="Manual fabrication RFQ"; Group="04_REFERANS_PARTGOYA_YUKLEME"; Source="cad\test_stand\VIS-001\VIS-001.step"; Target="VIS-001_REFERENCE_ASSEMBLY.step"; Status="REFERENCE_MULTI_BODY_DO_NOT_UPLOAD"},
    @{Part="CHA-001"; Qty=1; Material="Plywood or fixture plate"; Process="Router/saw"; Group="04_REFERANS_PARTGOYA_YUKLEME"; Source="cad\test_stand\CHA-001\CHA-001.dxf"; Target="CHA-001_REFERENCE_PLYWOOD.dxf"; Status="REFERENCE_MATERIAL_NOT_PARTGO_BASELINE"},
    @{Part="ARM-001-BLANK"; Qty=1; Material="EN AW-6082-T6 12 mm"; Process="2D blank reference"; Group="04_REFERANS_PARTGOYA_YUKLEME"; Source="cad\arm\ARM-001\ARM-001.dxf"; Target="ARM-001_REFERENCE_BLANK.dxf"; Status="REFERENCE_USE_STEP_FOR_CNC"},
    @{Part="FIGBOT-V0"; Qty=1; Material="Assembly"; Process="Reference"; Group="04_REFERANS_PARTGOYA_YUKLEME"; Source="cad\assembly\FIGBOT_V0_ASSEMBLY.step"; Target="FIGBOT_V0_ASSEMBLY_REFERENCE_DO_NOT_UPLOAD.step"; Status="REFERENCE_MULTI_BODY_DO_NOT_UPLOAD"},
    @{Part="FIGBOT-V1"; Qty=1; Material="Assembly concept"; Process="Reference"; Group="04_REFERANS_PARTGOYA_YUKLEME"; Source="cad\assembly\FIGBOT_V1_ASSEMBLY.step"; Target="FIGBOT_V1_ASSEMBLY_REFERENCE_DO_NOT_UPLOAD.step"; Status="REFERENCE_MULTI_BODY_DO_NOT_UPLOAD"}
)

$index = @()
foreach ($item in $items) {
    $source = Join-Path $root $item.Source
    if (-not (Test-Path -LiteralPath $source)) { throw "Missing CAD file: $source" }
    $folder = Join-Path $output $item.Group
    if (-not (Test-Path -LiteralPath $folder)) { New-Item -ItemType Directory -Path $folder | Out-Null }
    $target = Join-Path $folder $item.Target
    Copy-Item -LiteralPath $source -Destination $target
    $size = (Get-Item -LiteralPath $target).Length
    if ($size -le 0) { throw "Empty CAD file: $target" }
    if ($target.EndsWith(".step") -and $size -gt 50MB) { throw "STEP exceeds PartGo 50 MB limit: $target" }
    $index += [pscustomobject]@{
        part_number=$item.Part; quantity=$item.Qty; material=$item.Material; process=$item.Process
        folder=$item.Group; upload_filename=$item.Target; release_status=$item.Status; size_bytes=$size
    }
}

$drawings = Join-Path $output "04_REFERANS_PARTGOYA_YUKLEME\TEKNIK_RESIMLER"
New-Item -ItemType Directory -Path $drawings | Out-Null
Get-ChildItem -LiteralPath (Join-Path $root "cad") -Recurse -Filter "*_drawing.pdf" |
    ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination $drawings }

$index | Export-Csv -LiteralPath (Join-Path $output "PART_INDEX.csv") -NoTypeInformation -Encoding utf8
Copy-Item -LiteralPath (Join-Path $root "manufacturing\PARTGO_UPLOAD_INSTRUCTIONS_TR.md") -Destination (Join-Path $output "00_ONCE_BUNU_OKU.md")
Copy-Item -LiteralPath (Join-Path $root "manufacturing\INTERFACE_CONTROL.csv") -Destination $output

$zip = "$output-TRANSFER-ONLY-EXTRACT-FIRST.zip"
Compress-Archive -LiteralPath $output -DestinationPath $zip
Write-Output "DIRECT_FOLDER=$output"
Write-Output "TRANSFER_ZIP=$zip"
Write-Output "FILES=$($items.Count)"
