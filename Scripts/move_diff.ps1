# Per-frame mean absolute difference (0-255, far-layer band only) between each hybrid move and the v6 move.
# Ghosting / misregistration in the projected layer raises this curve; a flat low curve means the hybrid
# tracks the full-geometry render through the whole move. Uses the 960x540 web frames.
#   .\Scripts\move_diff.ps1  -> Renders/gateA_hybrid/move_diff.csv + move_diff.png
Add-Type -AssemblyName System.Drawing
$proj = Split-Path -Parent $PSScriptRoot
$W = "$proj\Renders\gateA_hybrid\web"
$rows = @()
function Pixels($path) {
    $bmp = [System.Drawing.Bitmap]::FromFile($path)
    $r = New-Object System.Drawing.Rectangle 0, 0, $bmp.Width, $bmp.Height
    $d = $bmp.LockBits($r, 'ReadOnly', [System.Drawing.Imaging.PixelFormat]::Format24bppRgb)
    $n = $d.Stride * $bmp.Height
    $buf = New-Object byte[] $n
    [System.Runtime.InteropServices.Marshal]::Copy($d.Scan0, $buf, 0, $n)
    $hh = $bmp.Height; $ww = $bmp.Width; $st = $d.Stride
    $bmp.UnlockBits($d); $bmp.Dispose()
    return @{ buf = $buf; stride = $st; h = $hh; w = $ww }
}
# Bands (fractions of width/height), all outside the mask (K0 product matte bbox: x 60.8-80.2 %, y 41.1-71.3 %):
#   left  : upper 45 %, left 58 %            sky, skyline, far bank (the original measurement)
#   right : upper 40 %, right 17 % (x >= 83 %)  the K1 proxy side-face region (hybrid v1's error was here)
#   top   : upper 30 %, full width           sky + skyline over the whole frame
$bands = @{ left = @(0.0, 0.58, 0.0, 0.45); right = @(0.83, 1.0, 0.0, 0.40); top = @(0.0, 1.0, 0.0, 0.30) }
function BandDiff($a, $b, $band) {
    [double]$sum = 0; [long]$cnt = 0
    $x0 = [int]($a.w * $band[0]) * 3; $x1 = [int]($a.w * $band[1]) * 3
    for ($y = [int]($a.h * $band[2]); $y -lt [int]($a.h * $band[3]); $y += 2) {
        $o = $y * $a.stride
        for ($x = $x0; $x -lt $x1; $x += 6) {
            $sum += [math]::Abs([int]$a.buf[$o + $x] - [int]$b.buf[$o + $x]) + [math]::Abs([int]$a.buf[$o + $x + 1] - [int]$b.buf[$o + $x + 1]) + [math]::Abs([int]$a.buf[$o + $x + 2] - [int]$b.buf[$o + $x + 2])
            $cnt += 3
        }
    }
    return [math]::Round($sum / $cnt, 2)
}
for ($f = 0; $f -lt 48; $f++) {
    $name = "f{0:D4}.jpg" -f $f
    $a = Pixels "$W\v6\$name"
    $line = [ordered]@{ frame = $f }
    foreach ($h in "hybrid1", "hybrid2") {
        $b = Pixels "$W\$h\$name"
        $line[$h] = BandDiff $a $b $bands.left
        $line["${h}_right"] = BandDiff $a $b $bands.right
        $line["${h}_top"] = BandDiff $a $b $bands.top
    }
    $rows += New-Object PSObject -Property $line
}
$rows | Export-Csv "$proj\Renders\gateA_hybrid\move_diff.csv" -NoTypeInformation
# plot
$bmp = New-Object System.Drawing.Bitmap -ArgumentList 960, 320
$g = [System.Drawing.Graphics]::FromImage($bmp); $g.Clear([System.Drawing.Color]::FromArgb(14, 13, 12)); $g.SmoothingMode = 'AntiAlias'
$font = New-Object System.Drawing.Font('Segoe UI', 10); $txt = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(233, 227, 216))
$max = [math]::Max(1, ($rows | ForEach-Object { [math]::Max([math]::Max($_.hybrid1, $_.hybrid1_right), [math]::Max($_.hybrid2, $_.hybrid2_right)) } | Measure-Object -Maximum).Maximum)
$g.DrawString("mean |hybrid - v6| per frame (0-255). solid = left band, dashed = right band (x>=83%, K1 side-face region). red = v1 single plate, green = v2 three plates. max=$max", $font, $txt, 8, 6)
foreach ($k in @(@("hybrid1", [System.Drawing.Color]::FromArgb(217, 100, 74)), @("hybrid2", [System.Drawing.Color]::FromArgb(127, 179, 122)),
                 @("hybrid1_right", [System.Drawing.Color]::FromArgb(217, 100, 74), 1), @("hybrid2_right", [System.Drawing.Color]::FromArgb(127, 179, 122), 1))) {
    $pen = New-Object System.Drawing.Pen ($k[1], 2)
    if ($k.Count -gt 2) { $pen.DashStyle = 'Dash' }
    $pts = @(); for ($f = 0; $f -lt 48; $f++) { $pts += New-Object System.Drawing.PointF (40 + $f * 18.5), (290 - ($rows[$f].($k[0]) / $max) * 240) }
    $g.DrawLines($pen, $pts)
}
foreach ($f in 0, 24, 47) { $g.DrawString("f$f", $font, $txt, 34 + $f * 18.5, 296) }
$g.Dispose(); $bmp.Save("$proj\Renders\gateA_hybrid\move_diff.png", [System.Drawing.Imaging.ImageFormat]::Png); $bmp.Dispose()
$rows | Where-Object { $_.frame % 6 -eq 0 -or $_.frame -eq 47 } | Format-Table -AutoSize | Out-String
"wrote move_diff.csv / move_diff.png"
