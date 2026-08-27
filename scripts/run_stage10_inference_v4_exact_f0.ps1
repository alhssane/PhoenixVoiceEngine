param(
    [string]$DiffSinger = 'D:\PhoenixVoiceEngine\external\DiffSinger-openvpi',
    [string]$Config = 'D:\PhoenixVoiceEngine\jobs\freed_joud_fixed_v2\phoenix_arabic_acoustic.yaml',
    [string]$Raw = 'D:\PhoenixVoiceEngine\jobs\freed_joud_fixed_v2\datasets\stage5_full_v4\raw',
    [string]$Exp = 'phoenix_freed_joud_fixed_v2_train_2000step',
    [int]$Ckpt = 2000,
    [string]$Ds = 'D:\PhoenixVoiceEngine\jobs\freed_joud_fixed_v2\inference\freed_joud_fixed_v2_stage10_v4_exact_f0.ds',
    [string]$Out = 'D:\PhoenixVoiceEngine\jobs\freed_joud_fixed_v2\inference\stage10_output_v4_exact_f0'
)

$ErrorActionPreference = 'Stop'
$python = 'D:\PhoenixVoiceEngine\.venv_phoenix_svs\Scripts\python.exe'
$prep = Join-Path $PSScriptRoot 'prepare_stage10_inference_v4_exact_f0.py'
$infer = Join-Path $DiffSinger 'scripts\infer.py'

foreach ($item in @(
    @{Name='Python';Path=$python},
    @{Name='DiffSinger';Path=$DiffSinger},
    @{Name='Config';Path=$Config},
    @{Name='Raw dataset';Path=$Raw},
    @{Name='Preparation script';Path=$prep},
    @{Name='Inference script';Path=$infer}
)) {
    if ([string]::IsNullOrWhiteSpace([string]$item.Path)) {
        throw "$($item.Name) path is empty."
    }
    if (-not (Test-Path -LiteralPath $item.Path)) {
        throw "$($item.Name) not found: $($item.Path)"
    }
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Ds) | Out-Null
New-Item -ItemType Directory -Force -Path $Out | Out-Null

Write-Host "[Phoenix] Stage10-V4: exact training F0 backend (Parselmouth) ..." -ForegroundColor Cyan
& $python $prep --diffsinger $DiffSinger --raw $Raw --config $Config --out $Ds
if ($LASTEXITCODE -ne 0) { throw 'Stage10-V4 DS preparation failed.' }

$old = Get-Location
$oldPy = $env:PYTHONPATH
try {
    Set-Location $DiffSinger
    $env:PYTHONPATH = $DiffSinger
    Write-Host "[Phoenix] Stage10-V4: acoustic inference from $Exp @ $Ckpt steps..." -ForegroundColor Cyan
    & $python $infer acoustic $Ds --exp $Exp --ckpt $Ckpt --lang ar --spk freed_joud_fixed_v2 --out $Out --title freed_joud_fixed_v2_stage10_v4_exact_f0 --steps 20 --seed 42
    if ($LASTEXITCODE -ne 0) { throw 'Stage10-V4 acoustic inference failed.' }
} finally {
    Set-Location $old
    $env:PYTHONPATH = $oldPy
}

Write-Host "[Phoenix] Stage10-V4 completed. Output folder: $Out" -ForegroundColor Green
