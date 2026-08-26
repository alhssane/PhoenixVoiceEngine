param(
    [Parameter(Mandatory=$true)][string]$Stage4,
    [Parameter(Mandatory=$false)][string]$Output = 'D:\PhoenixVoiceEngine\datasets\freed_joud_diffsinger_raw'
)

$python = 'D:\PhoenixVoiceEngine\.venv_phoenix_svs\Scripts\python.exe'
$script = Join-Path $PSScriptRoot 'build_diffsinger_dataset_stage5.py'
if (-not (Test-Path $python)) { throw "Phoenix SVS Python not found: $python" }
if (-not (Test-Path $script)) { throw "Stage5 Python script not found: $script" }

Write-Host '[Phoenix] Baking Arabic DiffSinger raw dataset...' -ForegroundColor Cyan
& $python $script --stage4 $Stage4 --output $Output
if ($LASTEXITCODE -ne 0) { throw 'Stage5 dataset bake failed.' }
Write-Host "[Phoenix] Dataset bake completed. Output: $Output" -ForegroundColor Green
