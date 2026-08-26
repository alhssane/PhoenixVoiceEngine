$ErrorActionPreference = 'Stop'

if ($args.Count -lt 1) { throw 'Usage: build_diffsinger_dataset_stage2.ps1 <Stage1Path> [OutputPath]' }

$stage1 = (Resolve-Path $args[0]).Path
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root '.venv_phoenix_gpu\Scripts\python.exe'
$output = if ($args.Count -ge 2) { $args[1] } else { Join-Path $root 'datasets\freed_joud_diffsinger_stage2' }

if (-not (Test-Path $python)) { throw "Phoenix GPU Python not found: $python" }
if (-not (Test-Path $stage1)) { throw "Stage1 dataset not found: $stage1" }

Write-Host '[Phoenix] Installing Stage2 dependencies...' -ForegroundColor Cyan
& $python -m pip install 'epitran>=1.25,<2' 'panphon>=0.21,<1'
if ($LASTEXITCODE -ne 0) { throw 'Stage2 dependency installation failed.' }

Write-Host '[Phoenix] Building Arabic phoneme + pitch staging...' -ForegroundColor Cyan
& $python (Join-Path $PSScriptRoot 'build_diffsinger_dataset_stage2.py') --stage1 $stage1 --output $output
if ($LASTEXITCODE -ne 0) { throw 'Stage2 dataset build failed.' }

Write-Host '[Phoenix] Stage2 completed.' -ForegroundColor Green
Write-Host ('Output: ' + (Resolve-Path $output).Path) -ForegroundColor Yellow
Write-Host '[Phoenix] Training remains blocked until MFA/forced alignment and DiffSinger phone-set validation are complete.' -ForegroundColor DarkYellow
