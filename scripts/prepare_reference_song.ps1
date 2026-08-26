$ErrorActionPreference = 'Stop'

$AudioPath = $args[0]
$ProjectName = if ($args.Count -gt 1) { $args[1] } else { 'freed_joud_reference' }
$ArtistName = if ($args.Count -gt 2) { $args[2] } else { 'freed_joud' }

if ([string]::IsNullOrWhiteSpace($AudioPath)) { throw 'AudioPath is required.' }

$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot '.venv_phoenix_gpu\Scripts\python.exe'
$requirements = Join-Path $projectRoot 'requirements\requirements.txt'
$branch = 'foundation-hardening'
$cacheRoot = Join-Path $projectRoot '.cache\foundation_sync'
$zipPath = Join-Path $projectRoot '.cache\foundation-hardening.zip'

if (-not (Test-Path $python)) { throw "Phoenix GPU Python not found: $python" }
if (-not (Test-Path $AudioPath)) { throw "Audio file not found: $AudioPath" }

$entryPoint = Join-Path $projectRoot 'src\pipeline\song_project_engine.py'
if (-not (Test-Path $entryPoint)) {
    Write-Host '[Phoenix] Syncing missing src tree from foundation branch...' -ForegroundColor DarkCyan
    New-Item -ItemType Directory -Path (Split-Path $zipPath -Parent) -Force | Out-Null
    if (Test-Path $cacheRoot) { Remove-Item $cacheRoot -Recurse -Force }
    Invoke-WebRequest -Uri "https://github.com/alhssane/PhoenixVoiceEngine/archive/refs/heads/$branch.zip" -OutFile $zipPath
    Expand-Archive -Path $zipPath -DestinationPath $cacheRoot -Force
    $repoDir = Get-ChildItem $cacheRoot -Directory | Select-Object -First 1
    if (-not $repoDir) { throw 'Could not locate extracted foundation branch.' }
    $sourceSrc = Join-Path $repoDir.FullName 'src'
    $targetSrc = Join-Path $projectRoot 'src'
    Get-ChildItem $sourceSrc -Recurse -File | ForEach-Object {
        $relative = $_.FullName.Substring($sourceSrc.Length).TrimStart('\','/')
        $destination = Join-Path $targetSrc $relative
        if (-not (Test-Path $destination)) {
            New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
            Copy-Item $_.FullName $destination
            Write-Host "[Phoenix] Added missing source: src\$relative" -ForegroundColor DarkCyan
        }
    }
}

if (-not (Test-Path $entryPoint)) { throw 'song_project_engine.py is still missing after source sync.' }

Write-Host '[Phoenix] Validating source import...' -ForegroundColor Cyan
& $python -c "import sys; sys.path.insert(0, r'$projectRoot'); import src.pipeline.song_project_engine; print('Source import: OK')"
if ($LASTEXITCODE -ne 0) { throw 'Phoenix source import failed.' }

Write-Host '[Phoenix] Installing/validating Phoenix runtime dependencies...' -ForegroundColor Cyan
& $python -m pip install -r $requirements
if ($LASTEXITCODE -ne 0) { throw 'Phoenix runtime dependency installation failed.' }

Write-Host '[Phoenix] Preparing reference song...' -ForegroundColor Cyan
& $python -c "import json,sys; from pathlib import Path; root=Path(r'$projectRoot'); sys.path.insert(0,str(root)); from src.pipeline.song_project_engine import SongProjectEngine; manifest=SongProjectEngine(root/'Projects').prepare(Path(r'$AudioPath'), r'$ProjectName', r'$ArtistName'); print(json.dumps(manifest, ensure_ascii=False, indent=2))"
if ($LASTEXITCODE -ne 0) { throw 'Reference preparation failed.' }

Write-Host '[Phoenix] Reference project prepared.' -ForegroundColor Green
Write-Host ("Project root: " + (Join-Path $projectRoot ('Projects\' + $ArtistName + ' - ' + $ProjectName))) -ForegroundColor Yellow
