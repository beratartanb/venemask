# Product-detail comparison boards: store photo vs path-traced render, mask scaled to the same height.
#   .\Scripts\compare_product.ps1 [-Render <png>] [-OutDir <dir>]
# Crops are hand-measured once per camera setup (see $renderCrop) and the photo mask bounds (photo 01 / 03).
param(
    [string]$Render = "$(Split-Path -Parent $PSScriptRoot)\Renders\pt_beauty\LS_Hero_PathTracer.0000.png",
    [string]$OutDir = "$(Split-Path -Parent $PSScriptRoot)\Renders\gateA"
)
Add-Type -AssemblyName System.Drawing
$proj = Split-Path -Parent $PSScriptRoot
$photos = "$proj\SourceAssets\casanova_bauta"
New-Item -ItemType Directory -Force $OutDir | Out-Null

function Load($path) { [System.Drawing.Image]::FromFile($path) }
function CropScale($img, $rect, $h) {
    [int]$w = $rect.Width * $h / $rect.Height
    [int]$hh = $h
    $bmp = New-Object System.Drawing.Bitmap -ArgumentList $w, $hh
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.InterpolationMode = 'HighQualityBicubic'
    $g.DrawImage($img, (New-Object System.Drawing.Rectangle 0, 0, $w, $h), $rect, 'Pixel')
    $g.Dispose()
    return $bmp
}
function Board($tiles, $labels, $path, $h = 700) {
    $pad = 16; $lab = 34
    [int]$W = ($tiles | ForEach-Object { $_.Width } | Measure-Object -Sum).Sum + $pad * ($tiles.Count + 1)
    [int]$H = $h + $pad * 2 + $lab
    $bmp = New-Object System.Drawing.Bitmap -ArgumentList $W, $H
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.Clear([System.Drawing.Color]::FromArgb(14, 13, 12))
    $font = New-Object System.Drawing.Font('Segoe UI', 13)
    $brush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(233, 227, 216))
    $x = $pad
    for ($i = 0; $i -lt $tiles.Count; $i++) {
        $g.DrawImage($tiles[$i], $x, $pad)
        $g.DrawString($labels[$i], $font, $brush, $x, $pad + $h + 6)
        $x += $tiles[$i].Width + $pad
    }
    $g.Dispose()
    $bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
    $bmp.Dispose()
    "wrote $path"
}

$r = Load $Render
$p1 = Load "$photos\01_42829468205139.jpg"
$p3 = Load "$photos\03_42829468237907.jpg"
# mask bounds: render (1920x1080 hero camera v6), photo 01 front 3/4, photo 03 side
$renderCrop = New-Object System.Drawing.Rectangle 1150, 430, 420, 360
$photo1Crop = New-Object System.Drawing.Rectangle 270, 600, 900, 780
$photo3Crop = New-Object System.Drawing.Rectangle 330, 640, 920, 720

$t = @((CropScale $p1 $photo1Crop 700), (CropScale $r $renderCrop 700), (CropScale $p3 $photo3Crop 700))
Board $t @("venemask.com photo 01 (front 3/4)", "Unreal 5.8 Path Tracer (same height)", "venemask.com photo 03 (side)") "$OutDir\compare_product_v6.png"

# detail: braid + crackle 3x
$t2 = @((CropScale $p1 (New-Object System.Drawing.Rectangle 420, 640, 460, 300) 480), (CropScale $r (New-Object System.Drawing.Rectangle 1170, 440, 400, 260) 480))
Board $t2 @("photo 01: brim braid + crackle", "render: brim braid + crackle") "$OutDir\compare_detail_v6.png" 480

# references vs render at equal width
$ref1 = Load "$proj\references\01-multi-mask-room-and-product-showcase.jpeg"
$ref2 = Load "$proj\references\02-venetian-hero-wide-space.jpeg"
$t3 = @((CropScale $ref2 (New-Object System.Drawing.Rectangle 0, 0, $ref2.Width, $ref2.Height) 540), (CropScale $r (New-Object System.Drawing.Rectangle 0, 0, $r.Width, $r.Height) 540))
Board $t3 @("reference 02 (art direction)", "Unreal 5.8 Path Tracer v6") "$OutDir\compare_reference_v6.png" 540
$r.Dispose(); $p1.Dispose(); $p3.Dispose(); $ref1.Dispose(); $ref2.Dispose()
