# Four-way K0/K1/K2 grid: concept reference | v6 full geometry | hybrid v1 (single plate) | hybrid v2 (3 plates).
# The reference is a single concept frame, so it is repeated on every row and labelled as such.
#   .\Scripts\compare_fourway.ps1
Add-Type -AssemblyName System.Drawing
$proj = Split-Path -Parent $PSScriptRoot
$H = "$proj\Renders\gateA_hybrid"
$ref2 = "$proj\references\02-venetian-hero-wide-space.jpeg"

function Load($path) { if (Test-Path $path) { [System.Drawing.Image]::FromFile($path) } else { $null } }
function Tile($img, $w, $h) {
    [int]$w = $w; [int]$h = $h
    $bmp = New-Object System.Drawing.Bitmap -ArgumentList $w, $h
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.Clear([System.Drawing.Color]::FromArgb(20, 18, 16))
    if ($img) {
        $g.InterpolationMode = 'HighQualityBicubic'
        $s = [math]::Min($w / $img.Width, $h / $img.Height)
        [int]$tw = $img.Width * $s; [int]$th = $img.Height * $s
        $g.DrawImage($img, [int](($w - $tw) / 2), [int](($h - $th) / 2), $tw, $th)
    } else { $g.DrawString("missing", (New-Object System.Drawing.Font('Segoe UI', 14)), [System.Drawing.Brushes]::Gray, 10, 10) }
    $g.Dispose(); return $bmp
}
$tw = 480; $th = 270; $pad = 10; $lab = 24
$cols = 4; $rows = 3
[int]$W = $cols * $tw + ($cols + 1) * $pad
[int]$Hh = $rows * ($th + $lab) + ($rows + 1) * $pad + 30
$bmp = New-Object System.Drawing.Bitmap -ArgumentList $W, $Hh
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.Clear([System.Drawing.Color]::FromArgb(14, 13, 12))
$font = New-Object System.Drawing.Font('Segoe UI', 10)
$fontH = New-Object System.Drawing.Font('Segoe UI', 12)
$brush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(233, 227, 216))
$g.DrawString("K0 / K1 / K2 - referans (tek konsept karesi) | v6 tam geometri | hibrit v1 tek plaka | hibrit v2 uc plaka (AI plakasi YOK: BLOCKED)", $fontH, $brush, $pad, 6)
$ref = Load $ref2
$r = 0
foreach ($k in "K0", "K1", "K2") {
    $srcs = @(
        @{ img = $ref; label = "referans 02 (tek kare, $k icin ayni)" },
        @{ img = (Load "$H\stills\L_Hero_LS_${k}_PathTracer.0000.png"); label = "v6 tam geometri - $k" },
        @{ img = (Load "$H\stills_singleplate\L_Hero_Hybrid_LS_${k}_Hybrid_PathTracer.0000.png"); label = "hibrit v1 (tek plaka) - $k" },
        @{ img = (Load "$H\stills\L_Hero_Hybrid_LS_${k}_Hybrid_PathTracer.0000.png"); label = "hibrit v2.2 (3 plaka, linear) - $k" }
    )
    for ($c = 0; $c -lt 4; $c++) {
        $x = $pad + $c * ($tw + $pad); $y = 30 + $pad + $r * ($th + $lab + $pad)
        $t = Tile $srcs[$c].img $tw $th
        $g.DrawImage($t, $x, $y); $t.Dispose()
        $g.DrawString($srcs[$c].label, $font, $brush, $x, $y + $th + 3)
        if ($c -gt 0 -and $srcs[$c].img) { $srcs[$c].img.Dispose() }
    }
    $r++
}
$g.Dispose()
$bmp.Save("$H\compare_fourway_K012.png", [System.Drawing.Imaging.ImageFormat]::Png); $bmp.Dispose(); $ref.Dispose()
"wrote $H\compare_fourway_K012.png"
