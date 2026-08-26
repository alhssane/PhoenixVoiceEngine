$ErrorActionPreference = 'Stop'

if ($args.Count -lt 1) {
    throw 'Usage: build_diffsinger_dataset_stage4_ar.ps1 <Stage3Path> [OutputPath]'
}

$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot '.venv_phoenix_svs\Scripts\python.exe'
$stage3 = (Resolve-Path $args[0]).Path
$output = if ($args.Count -ge 2) { $args[1] } else { Join-Path $projectRoot 'datasets\freed_joud_diffsinger_stage4_ar' }
$script = Join-Path $PSScriptRoot 'build_diffsinger_dataset_stage4_ar.py'

if (-not (Test-Path $python)) { throw "Phoenix SVS Python not found: $python" }
if (-not (Test-Path $stage3)) { throw "Stage3 path not found: $stage3" }
if (-not (Test-Path $script)) { throw "Arabic Stage4 script not found: $script" }

Write-Host '[Phoenix] Building Arabic-native DiffSinger phone-set dataset...' -ForegroundColor Cyan
& $python $script --stage3 $stage3 --output $output
if ($LASTEXITCODE -ne 0) { throw 'Arabic Stage4 build failed.' }

Write-Host '[Phoenix] Arabic phone-set dataset created.' -ForegroundColor Green
Write-Host ("Output: " + (Resolve-Path $output).Path) -ForegroundColor Yellow
Write-Host '[Phoenix] Training remains blocked until DiffSinger dataset preprocessing and validation pass.' -ForegroundColor DarkYellow
