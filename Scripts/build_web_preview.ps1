# Complete web preview of the K0->K1->K2 camera test (frames as 960x540 JPEG, committed to the repo).
#   .\Scripts\build_web_preview.ps1
Add-Type -AssemblyName System.Drawing
$proj = Split-Path -Parent $PSScriptRoot
$H = "$proj\Renders\gateA_hybrid"
$W = "$H\web"
$sets = @(
    @{ key = "v6";          src = "$H\move";             pat = "L_Hero_LS_Move_PathTracer.{0:D4}.png";               label = "v6 tam geometri" },
    @{ key = "hybrid1";     src = "$H\move_singleplate"; pat = "L_Hero_Hybrid_LS_Move_Hybrid_PathTracer.{0:D4}.png"; label = "hibrit v1 (tek plaka)" },
    @{ key = "hybrid2";     src = "$H\move";             pat = "L_Hero_Hybrid_LS_Move_Hybrid_PathTracer.{0:D4}.png"; label = "hibrit v2.2 (3 plaka, scene-linear plaka, kamera-mesafe karisimi)" }
)
$enc = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq 'image/jpeg' }
$ep = New-Object System.Drawing.Imaging.EncoderParameters 1
$ep.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter ([System.Drawing.Imaging.Encoder]::Quality, [long]82)
foreach ($s in $sets) {
    $out = "$W\$($s.key)"
    New-Item -ItemType Directory -Force $out | Out-Null
    $n = 0
    for ($f = 0; $f -lt 48; $f++) {
        $src = Join-Path $s.src ($s.pat -f $f)
        if (-not (Test-Path $src)) { continue }
        $img = [System.Drawing.Image]::FromFile($src)
        $bmp = New-Object System.Drawing.Bitmap -ArgumentList 960, 540
        $g = [System.Drawing.Graphics]::FromImage($bmp); $g.InterpolationMode = 'HighQualityBicubic'
        $g.DrawImage($img, 0, 0, 960, 540); $g.Dispose()
        $bmp.Save(("$out\f{0:D4}.jpg" -f $f), $enc, $ep); $bmp.Dispose(); $img.Dispose(); $n++
    }
    "$($s.key): $n frames"
}
$html = @"
<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Venemask K0-K1-K2</title>
<style>body{margin:0;background:#0e0d0c;color:#e9e3d8;font:14px system-ui}main{max-width:1500px;margin:0 auto;padding:16px}
.row{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px}img{width:100%;display:block;border:1px solid #2a2622;background:#000}
input{width:100%}label{color:#9a9184;display:block;margin-bottom:4px}button{background:#2a2622;color:#e9e3d8;border:0;padding:6px 14px;margin-right:8px}
@media(max-width:900px){.row{grid-template-columns:1fr}}</style></head><body><main>
<h2 style="font-weight:400">K0 → K1 → K2 kamera testi · 48 kare · Path Tracer 96 spp · aynı Casanova maskesi, aynı ışık</h2>
<p style="color:#9a9184">Kare 0 = K0 (v6 hero) · 24 = K1 (45 cm sola) · 47 = K2 (35 cm dolly-in + ~5° yaw). Oynat / kaydır.</p>
<div class="row">
<div><label>v6 tam geometri</label><img id="a"></div>
<div><label>hibrit v1 — tek plaka (K1'de proxy yan yüzü hatası)</label><img id="b"></div>
<div><label>hibrit v2.2 — 3 plaka, scene-linear plaka, kamera-mesafe karışımı</label><img id="c"></div>
</div>
<p><button id="play">Oynat</button><span id="t"></span></p>
<input id="s" type="range" min="0" max="47" value="0">
<script>
const s=document.getElementById('s'),t=document.getElementById('t'),imgs={a:'v6',b:'hybrid1',c:'hybrid2'};let timer=null;
function u(){const f=String(s.value).padStart(4,'0');for(const k in imgs)document.getElementById(k).src=imgs[k]+'/f'+f+'.jpg';
t.textContent=' frame '+String(s.value).padStart(2,'0')+' · '+(s.value==0?'K0':s.value<24?'K0→K1':s.value==24?'K1':s.value<47?'K1→K2':'K2');}
s.oninput=u;u();
document.getElementById('play').onclick=function(){if(timer){clearInterval(timer);timer=null;this.textContent='Oynat';return;}
this.textContent='Durdur';timer=setInterval(()=>{s.value=(+s.value+1)%48;u();},1000/12);};
for(const k in imgs)for(let f=0;f<48;f++){const i=new Image();i.src=imgs[k]+'/f'+String(f).padStart(4,'0')+'.jpg';}
</script></main></body></html>
"@
Set-Content "$W\index.html" $html -Encoding utf8
"wrote $W\index.html"
