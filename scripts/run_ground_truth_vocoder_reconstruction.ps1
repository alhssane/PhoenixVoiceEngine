param(
    [string]$DiffSinger = 'D:\PhoenixVoiceEngine\external\DiffSinger-openvpi',
    [string]$Config = 'D:\PhoenixVoiceEngine\jobs\freed_joud_fixed_v2\phoenix_arabic_acoustic.yaml',
    [string]$InputWav = 'D:\PhoenixVoiceEngine\jobs\freed_joud_fixed_v2\datasets\stage5_full_v4\raw\wavs\freed_joud_0000.wav',
    [string]$Output = 'D:\PhoenixVoiceEngine\jobs\freed_joud_fixed_v2\inference\ground_truth_vocoder\freed_joud_0000_reconstructed.wav'
)

$ErrorActionPreference = 'Stop'
$python = 'D:\PhoenixVoiceEngine\.venv_phoenix_svs\Scripts\python.exe'
$script = Join-Path $PSScriptRoot 'reconstruct_ground_truth_vocoder.py'

$required = @(
    @{ Name = 'Python'; Path = $python },
    @{ Name = 'Reconstruction script'; Path = $script },
    @{ Name = 'DiffSinger'; Path = $DiffSinger },
    @{ Name = 'Config'; Path = $Config },
    @{ Name = 'Input WAV'; Path = $InputWav }
)

foreach ($item in $required) {
    if ([string]::IsNullOrWhiteSpace([string]$item.Path)) {
        throw "$($item.Name) path is empty."
    }
    if (-not (Test-Path -LiteralPath $item.Path)) {
        throw "$($item.Name) path not found: $($item.Path)"
    }
}

if ([string]::IsNullOrWhiteSpace($Output)) {
    throw 'Output path is empty.'
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Output) | Out-Null

$oldPwd = Get-Location
$oldPyPath = $env:PYTHONPATH
try {
    Set-Location $DiffSinger
    $env:PYTHONPATH = $DiffSinger

    Write-Host '[Phoenix] Ground-truth vocoder reconstruction...' -ForegroundColor Cyan
    Write-Host "[Phoenix] Input:  $InputWav"
    Write-Host "[Phoenix] Output: $Output"

    & $python $script `
        --diffsinger $DiffSinger `
        --config $Config `
        --input $InputWav `
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
