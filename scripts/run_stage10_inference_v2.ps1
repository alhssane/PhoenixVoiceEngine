param(
    [string]$DiffSinger = 'D:\PhoenixVoiceEngine\external\DiffSinger-openvpi',
    [string]$Raw = 'D:\PhoenixVoiceEngine\jobs\freed_joud_fixed_v2\datasets\stage5_full_v4\raw',
    [string]$Exp = 'phoenix_freed_joud_fixed_v2_smoke_500step',
    [int]$Ckpt = 500,
    [string]$Ds = 'D:\PhoenixVoiceEngine\jobs\freed_joud_fixed_v2\inference\freed_joud_fixed_v2_stage10.ds',
    [string]$Out = 'D:\PhoenixVoiceEngine\jobs\freed_joud_fixed_v2\inference\stage10_output_500step'
)

$ErrorActionPreference = 'Stop'
$python = 'D:\PhoenixVoiceEngine\.venv_phoenix_svs\Scripts\python.exe'
$prep = Join-Path $PSScriptRoot 'prepare_stage10_inference.py'
$infer = Join-Path $DiffSinger 'scripts\infer.py'

foreach ($p in @($python, $prep, $infer, $Raw)) {
    if (-not (Test-Path $p)) { throw "Required path not found: $p" }
}

New-Item -ItemType Directory -Force -Path (Split-Path $Ds -Parent) | Out-Null
New-Item -ItemType Directory -Force -Path $Out | Out-Null

Write-Host "[Phoenix] Stage10-V2: building DS inference file from $Raw..." -ForegroundColor Cyan
& $python $prep --raw $Raw --out $Ds
if ($LASTEXITCODE -ne 0) { throw 'Stage10-V2 DS preparation failed.' }

$old = Get-Location
$oldPy = $env:PYTHONPATH
try {
    Set-Location $DiffSinger
    $env:PYTHONPATH = $DiffSinger
    Write-Host "[Phoenix] Stage10-V2: acoustic inference from $Exp @ $Ckpt steps..." -ForegroundColor Cyan
    & $python $infer acoustic $Ds --exp $Exp --ckpt $Ckpt --lang ar --spk freed_joud_fixed_v2 --out $Out --title freed_joud_fixed_v2_stage10 --steps 20 --seed 42
    if ($LASTEXITCODE -ne 0) { throw 'Stage10-V2 acoustic inference failed.' }
} finally {
    Set-Location $old
    $env:PYTHONPATH = $oldPy
}

Write-Host "[Phoenix] Stage10-V2 completed. Output folder: $Out" -ForegroundColor Green
