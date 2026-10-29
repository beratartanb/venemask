# Command-line Movie Render Queue render (no editor UI; exits when done).
#   .\Scripts\render.ps1 -Config MRQ_PT [-Sequence LS_Hero] [-Map L_Hero]
param(
    [Parameter(Mandatory = $true)][string]$Config,
    [string]$Sequence = "LS_Hero",
    [string]$Map = "L_Hero",
    # first pass after material changes: shaders compile on demand in -game and the frame
    # comes out with the default checker material; a warm-up run fills the shader cache
    [switch]$WarmUp
)
if ($WarmUp) { & $PSCommandPath -Config MRQ_Lumen -Sequence $Sequence -Map $Map | Out-Null }
$proj = Split-Path -Parent $PSScriptRoot
$ue = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
$log = "MRQ_$Config.log"
$args = @(
    "`"$proj\Venemask_Cinematic_Showroom.uproject`"",
    "/Game/Venemask/Maps/$Map",
    "-game",
    "-LevelSequence=/Game/Venemask/Cinematics/$Sequence.$Sequence",
    "-MoviePipelineConfig=/Game/Venemask/Cinematics/Render/$Config.$Config",
    "-windowed", "-ResX=1280", "-ResY=720",
    "-RenderOffscreen", "-Unattended", "-NoSplash", "-nop4",
    "-log=$log"
)
$t0 = Get-Date
$p = Start-Process -FilePath $ue -ArgumentList $args -PassThru
$p | Wait-Process
"exit $($p.ExitCode) after $([math]::Round(((Get-Date) - $t0).TotalMinutes, 1)) min"
Get-Content "$proj\Saved\Logs\$log" | Select-String "LogMovieRenderPipeline: (Error|Warning)|Movie Pipeline completed|PIE Ended|Fatal" | Select-Object -Last 12 | ForEach-Object { $_.Line }
