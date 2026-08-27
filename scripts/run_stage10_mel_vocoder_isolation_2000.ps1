param(
    [string]$DiffSinger = 'D:\PhoenixVoiceEngine\external\DiffSinger-openvpi',
    [string]$Ds = 'D:\PhoenixVoiceEngine\jobs\freed_joud_fixed_v2\inference\freed_joud_fixed_v2_stage10_2000.ds',
    [string]$Exp = 'phoenix_freed_joud_fixed_v2_train_2000step',
    [int]$Ckpt = 2000,
    [string]$Out = 'D:\PhoenixVoiceEngine\jobs\freed_joud_fixed_v2\inference\vocoder_isolation_2000step'
)

$ErrorActionPreference = 'Stop'
$python = 'D:\PhoenixVoiceEngine\.venv_phoenix_svs\Scripts\python.exe'
$infer = Join-Path $DiffSinger 'scripts\infer.py'
$vocode = Join-Path $DiffSinger 'scripts\vocode.py'

foreach ($p in @($python, $infer, $vocode, $Ds)) {
    if (-not (Test-Path $p)) { throw "Required path not found: $p" }
}

New-Item -ItemType Directory -Force -Path $Out | Out-Null

$oldPwd = Get-Location
$oldPy = $env:PYTHONPATH
try {
    Set-Location $DiffSinger
    $env:PYTHONPATH = $DiffSinger

    Write-Host '[Phoenix] Isolation: generating MEL only from Acoustic model...' -ForegroundColor Cyan
    & $python $infer acoustic $Ds `
        --exp $Exp `
        --ckpt $Ckpt `
        --lang ar `
        --spk freed_joud_fixed_v2 `
        --out $Out `
        --title freed_joud_fixed_v2_acoustic_2000 `
        --steps 20 `
        --seed 42 `
        --mel
    if ($LASTEXITCODE -ne 0) { throw 'MEL generation failed.' }

    $mel = Join-Path $Out 'freed_joud_fixed_v2_acoustic_2000.mel.pt'
    if (-not (Test-Path $mel)) {
        $mel = Get-ChildItem $Out -Filter '*.mel.pt' | Select-Object -First 1 -ExpandProperty FullName
    }
    if (-not $mel) { throw "MEL output not found in $Out" }

    Write-Host "[Phoenix] Isolation: vocoding MEL only with PC-NSF-HiFiGAN..." -ForegroundColor Cyan
    & $python $vocode $mel `
        --exp $Exp `
        --out $Out `
        --title freed_joud_vocoder_only_2000
    if ($LASTEXITCODE -ne 0) { throw 'Vocoder-only reconstruction failed.' }

    Write-Host "[Phoenix] Isolation completed. MEL: $mel" -ForegroundColor Green
    Write-Host "[Phoenix] Vocoder-only WAV: $(Join-Path $Out 'freed_joud_vocoder_only_2000.wav')" -ForegroundColor Green
}
finally {
    Set-Location $oldPwd
    $env:PYTHONPATH = $oldPy
}
