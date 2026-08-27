param(
    [string]$DiffSinger = 'D:\PhoenixVoiceEngine\external\DiffSinger-openvpi',
    [string]$Config = 'D:\PhoenixVoiceEngine\jobs\freed_joud_fixed_v2\phoenix_arabic_acoustic.yaml',
    [string]$Ds = 'D:\PhoenixVoiceEngine\jobs\freed_joud_fixed_v2\inference\freed_joud_fixed_v2_stage10_2000.ds',
    [string]$Exp = 'phoenix_freed_joud_fixed_v2_train_2000step',
    [int]$Ckpt = 2000,
    [string]$SourceWav = 'D:\PhoenixVoiceEngine\jobs\freed_joud_fixed_v2\datasets\stage5_full_v4\raw\wavs\freed_joud_0000.wav',
    [string]$Out = 'D:\PhoenixVoiceEngine\jobs\freed_joud_fixed_v2\inference\mel_diagnostic_2000step'
)

$ErrorActionPreference = 'Stop'
$python = 'D:\PhoenixVoiceEngine\.venv_phoenix_svs\Scripts\python.exe'
$infer = Join-Path $DiffSinger 'scripts\infer.py'
$audit = Join-Path $PSScriptRoot 'audit_acoustic_mel_match.py'

$required = @($python, $infer, $audit, $Config, $Ds, $SourceWav)
foreach ($path in $required) {
    if (-not (Test-Path -LiteralPath $path)) { throw "Required path not found: $path" }
}

New-Item -ItemType Directory -Force -Path $Out | Out-Null
$oldPwd = Get-Location
$oldPy = $env:PYTHONPATH
try {
    Set-Location $DiffSinger
    $env:PYTHONPATH = $DiffSinger

    Write-Host "[Phoenix] Stage10-MEL: extracting predicted MEL from $Exp @ $Ckpt..." -ForegroundColor Cyan
    & $python $infer acoustic $Ds --exp $Exp --ckpt $Ckpt --lang ar --spk freed_joud_fixed_v2 --out $Out --title freed_joud_fixed_v2_predicted --steps 20 --seed 42 --mel
    if ($LASTEXITCODE -ne 0) { throw 'Predicted MEL extraction failed.' }

    $pred = Join-Path $Out 'freed_joud_fixed_v2_predicted.mel.pt'
    if (-not (Test-Path -LiteralPath $pred)) { throw "Predicted MEL file not found: $pred" }

    $report = Join-Path $Out 'acoustic_mel_match_report.json'
    Write-Host '[Phoenix] Stage10-MEL: comparing predicted MEL vs ground-truth MEL...' -ForegroundColor Cyan
    & $python $audit --diffsinger $DiffSinger --config $Config --source-wav $SourceWav --pred-mel $pred --output $report
    if ($LASTEXITCODE -ne 0) { throw 'Acoustic MEL comparison failed.' }

    Write-Host "[Phoenix] Stage10-MEL diagnostic completed. Report: $report" -ForegroundColor Green
} finally {
    Set-Location $oldPwd
    $env:PYTHONPATH = $oldPy
}
