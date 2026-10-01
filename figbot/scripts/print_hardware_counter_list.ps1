$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$printRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\tmp\pdfs\hardware_counter'))
$receipt = Join-Path $printRoot 'PRINT_RECEIPT.json'
if (Test-Path -LiteralPath $receipt) { throw 'Print attempt already recorded; inspect receipt before any repeat.' }
$targetPrinter = 'Canon G3070 series'
$files = @((Join-Path $printRoot 'print-1.png'), (Join-Path $printRoot 'print-2.png'))
foreach ($file in $files) { if (!(Test-Path -LiteralPath $file)) { throw "Missing rendered page: $file" } }
$doc = New-Object System.Drawing.Printing.PrintDocument
$doc.PrinterSettings.PrinterName = $targetPrinter
if (!$doc.PrinterSettings.IsValid) { throw 'Printer is not valid.' }
$a4 = @($doc.PrinterSettings.PaperSizes | Where-Object { $_.Kind -eq [System.Drawing.Printing.PaperKind]::A4 })[0]
if (!$a4) { throw 'Printer does not expose A4.' }
$doc.DocumentName = 'FIGBOT HIRDAVATCI LISTESI - 2 A4 - L1.1'
$doc.PrinterSettings.Copies = 1
$doc.DefaultPageSettings.PaperSize = $a4
$doc.DefaultPageSettings.Landscape = $false
$doc.DefaultPageSettings.Color = $false
$doc.DefaultPageSettings.Margins = New-Object System.Drawing.Printing.Margins(0,0,0,0)
$doc.PrinterSettings.Duplex = [System.Drawing.Printing.Duplex]::Simplex
$doc.PrintController = New-Object System.Drawing.Printing.StandardPrintController
$script:counterPage = 0
$doc.add_PrintPage({
    param($sender, $e)
    $bitmap = [System.Drawing.Image]::FromFile($files[$script:counterPage])
    try {
        $e.Graphics.TranslateTransform(-$e.PageSettings.HardMarginX, -$e.PageSettings.HardMarginY)
        $e.Graphics.DrawImage($bitmap, [System.Drawing.RectangleF]::new(0,0,$e.PageSettings.PaperSize.Width,$e.PageSettings.PaperSize.Height))
    } finally { $bitmap.Dispose() }
    $script:counterPage++
    $e.HasMorePages = $script:counterPage -lt $files.Count
})
@{printer=$targetPrinter;status='SUBMISSION_STARTED';pages=2;copies=1;time=(Get-Date).ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath $receipt
try {
    $doc.Print()
    @{printer=$targetPrinter;status='PRINT_API_RETURNED';pages_rendered=$script:counterPage;copies=1;time=(Get-Date).ToString('o');physical_output_confirmed=$false} | ConvertTo-Json | Set-Content -LiteralPath $receipt
} catch {
    @{printer=$targetPrinter;status='UNCERTAIN_ERROR_DO_NOT_RETRY';error=$_.Exception.Message;pages_rendered=$script:counterPage;time=(Get-Date).ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath $receipt
    throw
} finally { $doc.Dispose() }
Get-Content -LiteralPath $receipt
