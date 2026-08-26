$ErrorActionPreference = 'Stop'
if ($args.Count -lt 1) { throw 'Usage: build_diffsinger_dataset_stage4.ps1 <Stage3Path> [DiffSingerRoot] [OutputPath]' }
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot '.venv_phoenix_svs\Scripts\python.exe'
$stage3 = (Resolve-Path $args[0]).Path
$diffRoot = if ($args.Count -ge 2) { (Resolve-Path $args[1]).Path } else { Join-Path $projectRoot 'external\DiffSinger-openvpi' }
$output = if ($args.Count -ge 3) { $args[2] } else { Join-Path $projectRoot 'datasets\freed_joud_diffsinger_stage4' }
$script = Join-Path $PSScriptRoot 'build_diffsinger_dataset_stage4.py'
if (-not (Test-Path $python)) { throw "Phoenix SVS Python not found: $python" }
if (-not (Test-Path $stage3)) { throw "Stage3 path not found: $stage3" }
if (-not (Test-Path $diffRoot)) { throw "DiffSinger root not found: $diffRoot" }
Write-Host '[Phoenix] Validating Stage3 phonemes against local DiffSinger dictionaries...' -ForegroundColor Cyan
& $python $script --stage3 $stage3 --diff-root $diffRoot --output $output
if ($LASTEXITCODE -ne 0) { throw 'Stage4 validation failed.' }
Write-Host '[Phoenix] Stage4 completed.' -ForegroundColor Green
Write-Host ("Output: " + (Resolve-Path $output).Path) -ForegroundColor Yellow
