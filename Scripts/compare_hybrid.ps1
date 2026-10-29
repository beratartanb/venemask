# Gate A-HYBRID comparison boards + camera-move contact sheets + an HTML scrubber.
#   .\Scripts\compare_hybrid.ps1
Add-Type -AssemblyName System.Drawing
$proj = Split-Path -Parent $PSScriptRoot
$S = "$proj\Renders\gateA_hybrid\stills"
$MV = "$proj\Renders\gateA_hybrid\move"
$OUT = "$proj\Renders\gateA_hybrid"
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
    } else {
        $g.DrawString("missing", (New-Object System.Drawing.Font('Segoe UI', 14)), [System.Drawing.Brushes]::Gray, 10, 10)
    }
    $g.Dispose(); return $bmp
}
function Grid($rows, $cols, $tiles, $labels, $path, $tw = 640, $th = 360) {
    $pad = 12; $lab = 26
    [int]$W = $cols * $tw + ($cols + 1) * $pad
    [int]$H = $rows * ($th + $lab) + ($rows + 1) * $pad
    $bmp = New-Object System.Drawing.Bitmap -ArgumentList $W, $H
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.Clear([System.Drawing.Color]::FromArgb(14, 13, 12))
    $font = New-Object System.Drawing.Font('Segoe UI', 11)
    $brush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(233, 227, 216))
    for ($r = 0; $r -lt $rows; $r++) {
        for ($c = 0; $c -lt $cols; $c++) {
            $i = $r * $cols + $c
            if ($i -ge $tiles.Count) { continue }
            $x = $pad + $c * ($tw + $pad); $y = $pad + $r * ($th + $lab + $pad)
            $g.DrawImage($tiles[$i], $x, $y)
            $g.DrawString($labels[$i], $font, $brush, $x, $y + $th + 4)
        }
    }
    $g.Dispose(); $bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png); $bmp.Dispose(); "wrote $path"
}

# --- K0/K1/K2: v6 full geometry (row 1) vs hybrid projection (row 2)
$tiles = @(); $labels = @()
foreach ($lvl in @(@("L_Hero", "", "v6 full geometry"), @("L_Hero_Hybrid", "_Hybrid", "hybrid A: 3D near + projected mid/far"))) {
    foreach ($k in "K0", "K1", "K2") {
        $img = Load "$S\$($lvl[0])_LS_$k$($lvl[1])_PathTracer.0000.png"
        $tiles += Tile $img 640 360; $labels += "$($lvl[2]) - $k"
        if ($img) { $img.Dispose() }
    }
}
Grid 2 3 $tiles $labels "$OUT\compare_K012_v6_vs_hybrid.png"

# --- reference 02 next to K0 of both
$r = Load $ref2
$t = @((Tile $r 640 360), (Tile (Load "$S\L_Hero_LS_K0_PathTracer.0000.png") 640 360), (Tile (Load "$S\L_Hero_Hybrid_LS_K0_Hybrid_PathTracer.0000.png") 640 360))
Grid 1 3 $t @("reference 02 (art direction)", "v6 full geometry K0", "hybrid A K0") "$OUT\compare_reference_K0.png"

# --- camera-move contact sheets (every 4th frame) for both levels
foreach ($lvl in @(@("L_Hero", "", "v6"), @("L_Hero_Hybrid", "_Hybrid", "hybridA"))) {
    $tiles = @(); $labels = @()
    for ($f = 0; $f -lt 48; $f += 4) {
        $img = Load ("$MV\$($lvl[0])_LS_Move$($lvl[1])_PathTracer.{0:D4}.png" -f $f)
        $tiles += Tile $img 426 240; $labels += ("frame {0:D2}" -f $f)
        if ($img) { $img.Dispose() }
    }
    Grid 3 4 $tiles $labels "$OUT\move_contact_$($lvl[2]).png" 426 240
}

# --- HTML scrubber: drag the slider to compare the two camera moves frame by frame
$html = @"
<!doctype html><html lang="tr"><head><meta charset="utf-8"><title>Venemask K0-K1-K2</title>
<style>body{margin:0;background:#0e0d0c;color:#e9e3d8;font:14px system-ui}main{max-width:1500px;margin:0 auto;padding:16px}
.row{display:grid;grid-template-columns:1fr 1fr;gap:12px}img{width:100%;display:block;border:1px solid #2a2622;background:#000}
input{width:100%}label{color:#9a9184}</style></head><body><main>
<h2 style="font-weight:400">K0 → K1 → K2 kamera testi · 48 kare · Path Tracer 96 spp · 1280×720</h2>
<div class="row"><div><label>v6 tam geometri</label><img id="a"></div><div><label>hibrit A (3D yakın + projeksiyon orta/uzak)</label><img id="b"></div></div>
<input id="s" type="range" min="0" max="47" value="0"><div id="t">frame 00 · K0</div>
<script>const s=document.getElementById('s'),a=document.getElementById('a'),b=document.getElementById('b'),t=document.getElementById('t');
function u(){const f=String(s.value).padStart(4,'0');a.src='move/L_Hero_LS_Move_PathTracer.'+f+'.png';b.src='move/L_Hero_Hybrid_LS_Move_Hybrid_PathTracer.'+f+'.png';
t.textContent='frame '+String(s.value).padStart(2,'0')+' · '+(s.value==0?'K0':s.value<24?'K0→K1 (yanal 45 cm)':s.value==24?'K1':s.value<47?'K1→K2 (dolly 35 cm + ~5° yaw)':'K2');}
s.oninput=u;u();</script></main></body></html>
"@
Set-Content "$OUT\camera_test.html" $html -Encoding utf8
"wrote $OUT\camera_test.html"
