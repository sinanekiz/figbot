# Original dimension schematic. Coordinates, arrow endpoints and labels are deterministic.
Add-Type -AssemblyName System.Drawing
$ErrorActionPreference = 'Stop'
$bitmap = New-Object System.Drawing.Bitmap 1600,1120
$g = [System.Drawing.Graphics]::FromImage($bitmap)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$g.Clear([System.Drawing.Color]::White)
$navy='#122B49'; $blue='#146AC8'; $orange='#DE6419'; $green='#147D59'; $grey='#708297'
function Pen($c,$w=3) { return [System.Drawing.Pen]::new([System.Drawing.ColorTranslator]::FromHtml($c),$w) }
function Brush($c) { return [System.Drawing.SolidBrush]::new([System.Drawing.ColorTranslator]::FromHtml($c)) }
function Txt($s,$x,$y,$size=25,$c=$navy,$bold=$false) {
    $style=if($bold){[System.Drawing.FontStyle]::Bold}else{[System.Drawing.FontStyle]::Regular}
    $font=[System.Drawing.Font]::new('Arial',$size,$style,[System.Drawing.GraphicsUnit]::Pixel)
    $b=Brush $c; $g.DrawString($s,$font,$b,[single]$x,[single]$y); $font.Dispose();$b.Dispose()
}
function Line($x1,$y1,$x2,$y2,$c=$navy,$w=3,$dash=$false) {
    $p=Pen $c $w;if($dash){$p.DashStyle=[System.Drawing.Drawing2D.DashStyle]::Dash}
    $g.DrawLine($p,[single]$x1,[single]$y1,[single]$x2,[single]$y2);$p.Dispose()
}
function Arrow($x1,$y1,$x2,$y2,$c) {
    $p=Pen $c 4; $cap=[System.Drawing.Drawing2D.AdjustableArrowCap]::new(4,5)
    $p.CustomStartCap=$cap;$p.CustomEndCap=$cap
    $g.DrawLine($p,[single]$x1,[single]$y1,[single]$x2,[single]$y2);$p.Dispose();$cap.Dispose()
}
function Rect($x,$y,$w,$h,$fill,$stroke=$navy) {
    $b=Brush $fill;$p=Pen $stroke 2;$g.FillRectangle($b,$x,$y,$w,$h);$g.DrawRectangle($p,$x,$y,$w,$h);$b.Dispose();$p.Dispose()
}
function Dot($x,$y,$r,$c) {$b=Brush $c;$g.FillEllipse($b,($x-$r),($y-$r),(2*$r),(2*$r));$b.Dispose()}
function Badge($n,$x,$y,$c) {Dot $x $y 22 $c;Txt "$n" ($x-9) ($y-17) 29 '#FFFFFF' $true}
function Panel($x,$y,$w,$h,$name) {Rect $x $y $w $h '#FFFFFF' '#BDCBD9';Rect $x $y $w 55 '#EAF2FA' '#EAF2FA';Txt $name ($x+20) ($y+12) 27 $navy $true}

Txt 'NEREYİ ÖLÇECEĞİM?' 35 20 42 $navy $true
Txt 'Değerleri santimetre (cm) olarak buraya yaz. Uygulamaya girmen gerekmiyor.' 35 78 27
Panel 25 130 740 475 'ÜSTTEN BAKIŞ • Sepetin yeri ve boyutu'
Panel 790 130 785 475 'YANDAN BAKIŞ • Sepetin yüksekliği'
Panel 25 625 1550 360 'İNCİRİN BULUNDUĞU YÜZEY'

# Top view: O=(210,510), T=(210,310), S=(590,310). Exact orthogonal dimensions.
Txt 'Ön = incir toplama yönü ↑' 55 203 25
$p=Pen '#A4B5C7' 3;$g.DrawEllipse($p,165,465,90,90);$p.Dispose()
$b=Brush '#F1F8F3';$g.FillEllipse($b,490,210,200,200);$b.Dispose()
$p=Pen $green 5;$g.DrawEllipse($p,490,210,200,200);$p.Dispose()
Arrow 210 510 210 310 $orange
Arrow 210 310 590 310 $blue
Line 210 310 225 310 $grey 2
Line 225 310 225 325 $grey 2
Line 225 325 210 325 $grey 2
Badge 1 140 405 $orange;Txt 'Öne' 57 439 25 $orange;Txt 'mesafe' 57 469 25 $orange
Badge 2 352 272 $blue;Txt 'Yana mesafe' 385 254 25 $blue
Arrow 519.29 239.29 660.71 380.71 $green
Badge 3 575 445 $green;Txt 'Sepet iç çapı' 605 430 23 $green
Dot 210 510 8 '#CA3548';Txt 'O' 198 544 27 $navy $true
Dot 590 310 8 $navy;Txt 'S: merkez' 556 339 22 $navy $true
Txt 'Tabanın dönme merkezi' 54 576 22
Txt 'Sol ←      → Sağ (öne bakarken)' 355 530 22

# Side view: common mount plane y=500, inner floor y=440, upper rim y=290.
Rect 810 500 740 25 '#E3D3B8' '#A39075'
Line 810 500 1550 500 $navy 2 $true
Rect 847 445 72 55 '#DBE5EF'
Line 883 445 890 329 $orange 19
Line 890 329 1000 245 $orange 19
Line 1000 245 1090 350 $orange 19
Dot 890 329 15 $navy;Dot 1000 245 15 $navy
Line 1090 350 1128 340 $navy 7;Line 1090 350 1118 380 $navy 7
Dot 883 500 8 '#CA3548';Txt 'O' 870 535 27 $navy $true
Rect 1230 290 205 210 '#FAF2E4' '#997A49'
Rect 1242 300 181 140 '#FFFFFF' '#997A49'
Line 1230 290 1545 290 $grey 2 $true
Line 1160 440 1430 440 $grey 2 $true
Arrow 1170 500 1170 440 $orange
Badge 4 1126 465 $orange
Arrow 1500 500 1500 290 $blue
Badge 5 1537 387 $blue
Txt 'İç taban' 1260 446 23 $orange
Txt 'Üst kenar' 1245 255 23 $blue
Txt '4: İç tabana kadar' 930 538 23 $orange
Txt '5: Üst kenara kadar' 1270 538 23 $blue
Txt 'İkisi de kolun sabitlendiği yüzeyden ölçülür.' 935 572 22

# Lower scene: mount surface y=775, fruit surface y=925; fruit top y=840.
Rect 50 775 530 30 '#E3D3B8' '#A39075'
Rect 95 724 86 51 '#DBE5EF'
Txt 'Kolun sabitlendiği yüzey = 0' 220 727 25 $navy $true
Line 50 775 740 775 $navy 2 $true
Rect 580 925 460 25 '#E3D3B8' '#A39075'
Arrow 660 775 660 925 $orange;Badge 6 708 850 $orange
$b=Brush '#8D5484';$g.FillEllipse($b,825,855,85,70);$b.Dispose()
Line 866 855 870 840 '#557640' 8
Line 870 840 996 840 $grey 2 $true
Arrow 960 925 960 840 $blue;Badge 7 1002 877 $blue
Txt '6: Yüzeyler arasındaki yükseklik farkı.' 1080 724 23 $orange $true
Txt 'Aşağı mı, yukarı mı olduğunu belirt.' 1080 760 22
Txt 'Aynı masadaysa 6 = 0.' 1080 792 24 $navy $true
Txt '7: İncirin altından tepesine kadar.' 1080 851 23 $blue $true
Txt 'Farklı boylar varsa küçük ve büyük' 1080 887 22
Txt 'birer inciri ölç.' 1080 917 22

Txt 'O: Tabanın dik dönme ekseninin, kolun sabitlendiği yüzeydeki noktası.' 40 1004 26 $navy $true
Txt '1 ve 2 sepetin MERKEZİNE göre ölçülür. Çapraz mesafe ölçme. Şema ölçekli değildir.' 40 1045 25
Txt 'Bunlar ilk ortam ölçüleridir; kamera–kol eşlemesi ayrıca doğrulanacaktır.' 40 1080 23 $grey
$output=Join-Path $PSScriptRoot '../software/st3215_test/OLCUM_REHBERI.png'
$bitmap.Save([IO.Path]::GetFullPath($output),[System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose();$bitmap.Dispose()
Write-Output ([IO.Path]::GetFullPath($output))
