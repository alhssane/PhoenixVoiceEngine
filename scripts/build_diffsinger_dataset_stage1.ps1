$ErrorActionPreference = 'Stop'

if ($args.Count -lt 1) {
    throw 'Usage: build_diffsinger_dataset_stage1.ps1 <ProjectPath> [OutputPath]'
}

$project = (Resolve-Path $args[0]).Path
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot '.venv_phoenix_gpu\Scripts\python.exe'
$output = if ($args.Count -ge 2) { $args[1] } else { Join-Path $projectRoot 'datasets\freed_joud_diffsinger_stage1' }

if (-not (Test-Path $python)) { throw "Phoenix GPU Python not found: $python" }
if (-not (Test-Path $project)) { throw "Project not found: $project" }

Write-Host '[Phoenix] Building DiffSinger dataset staging...' -ForegroundColor Cyan
& $python (Join-Path $PSScriptRoot 'build_diffsinger_dataset_stage1.py') --project $project --output $output
if ($LASTEXITCODE -ne 0) { throw 'Dataset staging failed.' }

Write-Host '[Phoenix] Dataset staging completed.' -ForegroundColor Green
Write-Host ("Output: " + (Resolve-Path $output).Path) -ForegroundColor Yellow
Write-Host '[Phoenix] Training remains blocked until phoneme alignment and pitch labels are validated.' -ForegroundColor DarkYellow
