param(
    [string]$DiffSinger = 'D:\PhoenixVoiceEngine\external\DiffSinger-openvpi',
    [string]$Config = 'D:\PhoenixVoiceEngine\jobs\freed_joud_fixed_v2\phoenix_arabic_acoustic.yaml',
    [string]$Input = 'D:\PhoenixVoiceEngine\jobs\freed_joud_fixed_v2\datasets\stage5_full_v4\raw\wavs\freed_joud_0000.wav',
    [string]$Output = 'D:\PhoenixVoiceEngine\jobs\freed_joud_fixed_v2\inference\ground_truth_vocoder\freed_joud_0000_reconstructed.wav'
)

$ErrorActionPreference = 'Stop'
$python = 'D:\PhoenixVoiceEngine\.venv_phoenix_svs\Scripts\python.exe'
$script = Join-Path $PSScriptRoot 'reconstruct_ground_truth_vocoder.py'

foreach ($path in @($python, $script, $DiffSinger, $Config, $Input)) {
    if (-not (Test-Path $path)) { throw "Required path not found: $path" }
}

New-Item -ItemType Directory -Force -Path (Split-Path $Output -Parent) | Out-Null

$oldPwd = Get-Location
$oldPyPath = $env:PYTHONPATH
try {
    Set-Location $DiffSinger
    $env:PYTHONPATH = $DiffSinger

    Write-Host '[Phoenix] Ground-truth vocoder reconstruction...' -ForegroundColor Cyan
    Write-Host "[Phoenix] Input:  $Input"
    Write-Host "[Phoenix] Output: $Output"

    & $python $script `
        --diffsinger $DiffSinger `
        --config $Config `
        --input $Input `
        --output $Output

    if ($LASTEXITCODE -ne 0) {
        throw 'Ground-truth vocoder reconstruction failed.'
    }
}
finally {
    Set-Location $oldPwd
    $env:PYTHONPATH = $oldPyPath
}

Write-Host "[Phoenix] Ground-truth reconstruction completed: $Output" -ForegroundColor Green
