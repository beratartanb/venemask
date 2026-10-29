# Alignment / brightness check board for an externally generated K0 plate.
#   .\Scripts\check_ai_plate.ps1 -Ai Renders\plate\ai\K0_ai.png [-Out Renders\plate\ai\K0_ai_check.png]
# Board: AI plate | render beauty | AI with segmentation edges overlaid (green) | |AI - beauty| x3
# plus the horizon row and mean sRGB code of both images per band. Pure System.Drawing, 8-bit PNG input.
param(
    [Parameter(Mandatory = $true)][string]$Ai,
    [string]$Out = ""
)
Add-Type -AssemblyName System.Drawing
$proj = Split-Path -Parent $PSScriptRoot
$H = "$proj\Renders\plate\handoff_K0"
if (-not $Out) { $Out = [System.IO.Path]::ChangeExtension((Resolve-Path $Ai).Path, $null).TrimEnd('.') + "_check.png" }
$aimg = [System.Drawing.Bitmap]::FromFile((Resolve-Path $Ai).Path)
$bt = [System.Drawing.Bitmap]::FromFile("$H\K0_beauty_4096x2304_sRGB.png")
$sg = [System.Drawing.Bitmap]::FromFile("$H\K0_segmentation.png")
"AI plate: $($aimg.Width)x$($aimg.Height) $($aimg.PixelFormat); beauty: $($bt.Width)x$($bt.Height)"
if ($aimg.Width -ne $bt.Width -or $aimg.Height -ne $bt.Height) { "SIZE MISMATCH: expected $($bt.Width)x$($bt.Height)" }
$W = 960; $Hh = 540; $pad = 6; $hdr = 22
$board = New-Object System.Drawing.Bitmap -ArgumentList ([int](2 * ($W + $pad) + $pad)), ([int](2 * ($Hh + $hdr + $pad) + $pad + 60))
$g = [System.Drawing.Graphics]::FromImage($board); $g.Clear([System.Drawing.Color]::FromArgb(14, 13, 12)); $g.InterpolationMode = 'HighQualityBicubic'
$font = New-Object System.Drawing.Font('Segoe UI', 10); $txt = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(233, 227, 216))
function Small($b) { $s = New-Object System.Drawing.Bitmap -ArgumentList $W, $Hh; $gg = [System.Drawing.Graphics]::FromImage($s); $gg.InterpolationMode = 'HighQualityBicubic'; $gg.DrawImage($b, 0, 0, $W, $Hh); $gg.Dispose(); return $s }
$sai = Small $aimg; $sbt = Small $bt; $ssg = Small $sg
# segmentation edges (colour change between neighbours) drawn over the AI image
$ov = New-Object System.Drawing.Bitmap $sai
for ($y = 1; $y -lt $Hh - 1; $y++) { for ($x = 1; $x -lt $W - 1; $x++) {
        $c = $ssg.GetPixel($x, $y); $r = $ssg.GetPixel($x + 1, $y); $d = $ssg.GetPixel($x, $y + 1)
        if ([math]::Abs($c.R - $r.R) + [math]::Abs($c.G - $r.G) + [math]::Abs($c.B - $r.B) -gt 60 -or [math]::Abs($c.R - $d.R) + [math]::Abs($c.G - $d.G) + [math]::Abs($c.B - $d.B) -gt 60) { $ov.SetPixel($x, $y, [System.Drawing.Color]::FromArgb(0, 255, 80)) }
    } }
# difference
$df = New-Object System.Drawing.Bitmap -ArgumentList $W, $Hh
for ($y = 0; $y -lt $Hh; $y++) { for ($x = 0; $x -lt $W; $x++) { $a = $sai.GetPixel($x, $y); $b = $sbt.GetPixel($x, $y); $v = [math]::Min(255, 3 * ([math]::Abs($a.R - $b.R) + [math]::Abs($a.G - $b.G) + [math]::Abs($a.B - $b.B)) / 3); $df.SetPixel($x, $y, [System.Drawing.Color]::FromArgb([int]$v, [int]$v, [int]$v)) } }
$items = @(@("AI plate", $sai), @("render beauty (K0, 24 mm)", $sbt), @("AI plate + segmentation edges", $ov), @("|AI - beauty| x3", $df))
for ($i = 0; $i -lt 4; $i++) { $x = $pad + ($i % 2) * ($W + $pad); $y = $pad + [math]::Floor($i / 2) * ($Hh + $hdr + $pad); $g.DrawString($items[$i][0], $font, $txt, $x, $y); $g.DrawImage($items[$i][1], $x, $y + $hdr) }
# horizon line (45.7 %) on the AI panel, and band means
$hy = [int]($Hh * 0.457); $pen = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(255, 200, 0), 1); $g.DrawLine($pen, $pad, $pad + $hdr + $hy, $pad + $W, $pad + $hdr + $hy)
function BandMean($b, $fy0, $fy1) { [double]$s = 0; $n = 0; for ($y = [int]($Hh * $fy0); $y -lt [int]($Hh * $fy1); $y += 3) { for ($x = 0; $x -lt $W; $x += 3) { $c = $b.GetPixel($x, $y); $s += ($c.R + $c.G + $c.B) / 3; $n++ } }; return [math]::Round($s / $n, 1) }
$lines = @()
foreach ($band in @(@("sky 0-25%", 0.0, 0.25), @("skyline 25-46%", 0.25, 0.457), @("below horizon 46-100%", 0.457, 1.0))) { $lines += "$($band[0]): AI $(BandMean $sai $band[1] $band[2])  beauty $(BandMean $sbt $band[1] $band[2])" }
$y0 = 2 * ($Hh + $hdr + $pad) + $pad
$g.DrawString("mean sRGB code per band (0-255)  |  yellow line = expected horizon 45.7 %  |  " + ($lines -join "   |   "), $font, $txt, $pad, $y0 + 6)
$g.Dispose(); $board.Save($Out, [System.Drawing.Imaging.ImageFormat]::Png)
$lines; "wrote $Out"
$aimg.Dispose(); $bt.Dispose(); $sg.Dispose(); $board.Dispose()
