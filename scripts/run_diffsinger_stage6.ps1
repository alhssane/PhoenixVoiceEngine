param(
    [Parameter(Mandatory=$false)][string]$Raw = 'D:\PhoenixVoiceEngine\datasets\freed_joud_diffsinger_raw',
    [Parameter(Mandatory=$false)][string]$DiffSinger = 'D:\PhoenixVoiceEngine\external\DiffSinger-openvpi',
    [Parameter(Mandatory=$false)][string]$Config = 'D:\PhoenixVoiceEngine\configs\diffsinger\phoenix_arabic_acoustic.yaml',
    [Parameter(Mandatory=$false)][string]$Binary = 'D:\PhoenixVoiceEngine\datasets\freed_joud_diffsinger_binary'
)

$python = 'D:\PhoenixVoiceEngine\.venv_phoenix_svs\Scripts\python.exe'
$prep = Join-Path $PSScriptRoot 'prepare_diffsinger_stage6.py'
if (-not (Test-Path $python)) { throw "Phoenix SVS Python not found: $python" }
if (-not (Test-Path $prep)) { throw "Stage6 preparation script not found: $prep" }
if (-not (Test-Path $Raw)) { throw "Stage5 raw dataset not found: $Raw" }
if (-not (Test-Path $DiffSinger)) { throw "DiffSinger source not found: $DiffSinger" }

Write-Host '[Phoenix] Stage6: preparing Arabic DiffSinger config...' -ForegroundColor Cyan
& $python $prep --raw $Raw --diffsinger $DiffSinger --config $Config --binary $Binary
if ($LASTEXITCODE -ne 0) { throw 'Stage6 config preparation failed.' }

$binarize = Join-Path $DiffSinger 'scripts\binarize.py'
if (-not (Test-Path $binarize)) {
    $binarize = Join-Path $DiffSinger 'data_gen\binarize.py'
}
if (-not (Test-Path $binarize)) { throw "DiffSinger binarize.py not found under $DiffSinger" }

$oldPwd = Get-Location
$oldPyPath = $env:PYTHONPATH
try {
    Set-Location $DiffSinger
    $env:PYTHONPATH = $DiffSinger
    Write-Host "[Phoenix] Running DiffSinger binarizer: $binarize" -ForegroundColor Cyan
    & $python $binarize --config $Config
    if ($LASTEXITCODE -ne 0) { throw 'DiffSinger binarization failed.' }
}
finally {
    Set-Location $oldPwd
    $env:PYTHONPATH = $oldPyPath
}

if (-not (Test-Path $Binary)) { throw "Binarization exited successfully but binary output was not found: $Binary" }
Write-Host "[Phoenix] Stage6 binarization completed. Output: $Binary" -ForegroundColor Green
