$ErrorActionPreference = 'Stop'

if ($args.Count -lt 2) {
    throw 'Usage: build_diffsinger_dataset_stage3.ps1 <Stage1Path> <Stage2Path> [OutputPath]'
}

$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot '.venv_phoenix_svs\Scripts\python.exe'
$stage1 = (Resolve-Path $args[0]).Path
$stage2 = (Resolve-Path $args[1]).Path
$output = if ($args.Count -ge 3) { $args[2] } else { Join-Path $projectRoot 'datasets\freed_joud_diffsinger_stage3' }
$script = Join-Path $PSScriptRoot 'build_diffsinger_dataset_stage3.py'

if (-not (Test-Path $python)) { throw "Phoenix SVS Python not found: $python" }
if (-not (Test-Path $stage1)) { throw "Stage1 path not found: $stage1" }
if (-not (Test-Path $stage2)) { throw "Stage2 path not found: $stage2" }

Write-Host '[Phoenix] Installing Stage3 dependencies in Phoenix SVS environment...' -ForegroundColor Cyan
& $python -m pip install --disable-pip-version-check 'transformers>=4.40,<6' 'huggingface_hub>=0.30,<2' | Out-Host
if ($LASTEXITCODE -ne 0) { throw 'Stage3 dependency installation failed.' }

Write-Host '[Phoenix] Running Arabic phoneme CTC forced alignment...' -ForegroundColor Cyan
& $python $script --stage1 $stage1 --stage2 $stage2 --output $output
if ($LASTEXITCODE -ne 0) { throw 'Stage3 alignment failed.' }

Write-Host '[Phoenix] Stage3 completed.' -ForegroundColor Green
Write-Host ("Output: " + (Resolve-Path $output).Path) -ForegroundColor Yellow
Write-Host '[Phoenix] Training remains blocked until DiffSinger phone-set validation and final dataset checks pass.' -ForegroundColor DarkYellow
