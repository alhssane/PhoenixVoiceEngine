param(
    [string]$DiffSinger = 'D:\PhoenixVoiceEngine\external\DiffSinger-openvpi',
    [string]$Raw = 'D:\PhoenixVoiceEngine\jobs\freed_joud_full_auto\datasets\stage5_full_v3\raw',
    [string]$Exp = 'phoenix_freed_joud_full_auto_stage9_1000step',
    [int]$Ckpt = 1000,
    [string]$Ds = 'D:\PhoenixVoiceEngine\jobs\freed_joud_full_auto\inference\freed_joud_stage10.ds',
    [string]$Out = 'D:\PhoenixVoiceEngine\jobs\freed_joud_full_auto\inference\stage10_output'
)

$ErrorActionPreference = 'Stop'
$python='D:\PhoenixVoiceEngine\.venv_phoenix_svs\Scripts\python.exe'
$prep=Join-Path $PSScriptRoot 'prepare_stage10_inference.py'
$infer=Join-Path $DiffSinger 'scripts\infer.py'

foreach($p in @($python,$prep,$infer,$Raw)){
    if(-not(Test-Path $p)){throw "Required path not found: $p"}
}

New-Item -ItemType Directory -Force -Path (Split-Path $Ds -Parent) | Out-Null
New-Item -ItemType Directory -Force -Path $Out | Out-Null

Write-Host '[Phoenix] Stage10: building DS inference file from current Song Job Dataset...' -ForegroundColor Cyan
& $python $prep --raw $Raw --out $Ds
if($LASTEXITCODE -ne 0){throw 'Stage10 DS preparation failed.'}

$old=(Get-Location)
$oldPy=$env:PYTHONPATH
try{
    Set-Location $DiffSinger
    $env:PYTHONPATH=$DiffSinger
    Write-Host "[Phoenix] Stage10: running acoustic inference from $Exp @ $Ckpt steps..." -ForegroundColor Cyan
    & $python $infer acoustic $Ds --exp $Exp --ckpt $Ckpt --lang ar --spk freed_joud --out $Out --title freed_joud_stage10 --steps 20 --seed 42
    if($LASTEXITCODE -ne 0){throw 'Stage10 acoustic inference failed.'}
}finally{
    Set-Location $old
    $env:PYTHONPATH=$oldPy
}

Write-Host "[Phoenix] Stage10 completed. Output folder: $Out" -ForegroundColor Green
