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
# far-layer band: upper 45% of the frame, left 58% (sky, skyline, far bank), excludes the mask and pier
for ($f = 0; $f -lt 48; $f++) {
    $name = "f{0:D4}.jpg" -f $f
    $a = Pixels "$W\v6\$name"
    $line = [ordered]@{ frame = $f }
    foreach ($h in "hybrid1", "hybrid2") {
        $b = Pixels "$W\$h\$name"
        [double]$sum = 0; [long]$cnt = 0
        for ($y = 0; $y -lt [int]($a.h * 0.45); $y += 2) {
            $o = $y * $a.stride
            for ($x = 0; $x -lt [int]($a.w * 0.58) * 3; $x += 6) {
                $sum += [math]::Abs([int]$a.buf[$o + $x] - [int]$b.buf[$o + $x]) + [math]::Abs([int]$a.buf[$o + $x + 1] - [int]$b.buf[$o + $x + 1]) + [math]::Abs([int]$a.buf[$o + $x + 2] - [int]$b.buf[$o + $x + 2])
                $cnt += 3
            }
        }
        $line[$h] = [math]::Round($sum / $cnt, 2)
    }
    $rows += New-Object PSObject -Property $line
}
$rows | Export-Csv "$proj\Renders\gateA_hybrid\move_diff.csv" -NoTypeInformation
# plot
$bmp = New-Object System.Drawing.Bitmap -ArgumentList 960, 320
$g = [System.Drawing.Graphics]::FromImage($bmp); $g.Clear([System.Drawing.Color]::FromArgb(14, 13, 12)); $g.SmoothingMode = 'AntiAlias'
$font = New-Object System.Drawing.Font('Segoe UI', 10); $txt = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(233, 227, 216))
$max = [math]::Max(1, ($rows | ForEach-Object { [math]::Max($_.hybrid1, $_.hybrid2) } | Measure-Object -Maximum).Maximum)
$g.DrawString("mean |hybrid - v6| in the far-layer band, per frame (0-255). red = hybrid v1 single plate, green = hybrid v2 three plates. max=$max", $font, $txt, 8, 6)
foreach ($k in @(@("hybrid1", [System.Drawing.Color]::FromArgb(217, 100, 74)), @("hybrid2", [System.Drawing.Color]::FromArgb(127, 179, 122)))) {
    $pen = New-Object System.Drawing.Pen ($k[1], 2)
    $pts = @(); for ($f = 0; $f -lt 48; $f++) { $pts += New-Object System.Drawing.PointF (40 + $f * 18.5), (290 - ($rows[$f].($k[0]) / $max) * 240) }
    $g.DrawLines($pen, $pts)
}
foreach ($f in 0, 24, 47) { $g.DrawString("f$f", $font, $txt, 34 + $f * 18.5, 296) }
$g.Dispose(); $bmp.Save("$proj\Renders\gateA_hybrid\move_diff.png", [System.Drawing.Imaging.ImageFormat]::Png); $bmp.Dispose()
$rows | Where-Object { $_.frame % 6 -eq 0 -or $_.frame -eq 47 } | Format-Table -AutoSize | Out-String
"wrote move_diff.csv / move_diff.png"
