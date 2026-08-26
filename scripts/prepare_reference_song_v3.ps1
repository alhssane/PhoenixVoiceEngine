$ErrorActionPreference = 'Stop'

if ($args.Count -lt 1) {
    throw 'Usage: prepare_reference_song_v3.ps1 <AudioPath> [ProjectName] [ArtistName]'
}

$AudioPath = $args[0]
$ProjectName = if ($args.Count -ge 2) { $args[1] } else { 'freed_joud_reference' }
$ArtistName = if ($args.Count -ge 3) { $args[2] } else { 'freed_joud' }

$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot '.venv_phoenix_gpu\Scripts\python.exe'
$requirements = Join-Path $projectRoot 'requirements\requirements.txt'

if (-not (Test-Path $python)) { throw "Phoenix GPU Python not found: $python" }
if (-not (Test-Path $AudioPath)) { throw "Audio file not found: $AudioPath" }

Write-Host '[Phoenix] Installing Phoenix runtime dependencies first...' -ForegroundColor Cyan
& $python -m pip install -r $requirements
if ($LASTEXITCODE -ne 0) { throw 'Phoenix runtime dependency installation failed.' }

Write-Host '[Phoenix] Verifying required Python modules...' -ForegroundColor Cyan
& $python -c "import librosa, soundfile, faster_whisper; print('Runtime imports: OK')"
if ($LASTEXITCODE -ne 0) { throw 'Required runtime modules are still unavailable.' }

Write-Host '[Phoenix] Syncing missing source tree from foundation branch...' -ForegroundColor DarkCyan
$cacheRoot = Join-Path $projectRoot '.cache\foundation_sync_v3'
$zipPath = Join-Path $projectRoot '.cache\foundation-hardening-v3.zip'
New-Item -ItemType Directory -Path (Split-Path $zipPath -Parent) -Force | Out-Null
if (Test-Path $cacheRoot) { Remove-Item $cacheRoot -Recurse -Force }
Invoke-WebRequest -Uri 'https://github.com/alhssane/PhoenixVoiceEngine/archive/refs/heads/foundation-hardening.zip' -OutFile $zipPath
Expand-Archive -Path $zipPath -DestinationPath $cacheRoot -Force
$repoDir = Get-ChildItem $cacheRoot -Directory | Select-Object -First 1
if (-not $repoDir) { throw 'Could not locate extracted foundation branch.' }

$sourceSrc = Join-Path $repoDir.FullName 'src'
$targetSrc = Join-Path $projectRoot 'src'
Get-ChildItem $sourceSrc -Recurse -File | ForEach-Object {
    $relative = $_.FullName.Substring($sourceSrc.Length).TrimStart('\','/')
    $destination = Join-Path $targetSrc $relative
    if (-not (Test-Path $destination)) {
        $destinationDir = Split-Path -Parent $destination
        New-Item -ItemType Directory -Path $destinationDir -Force | Out-Null
        Copy-Item $_.FullName $destination
        Write-Host "[Phoenix] Added missing source: src\$relative" -ForegroundColor DarkCyan
    }
}

Write-Host '[Phoenix] Validating source import...' -ForegroundColor Cyan
$rootEscaped = $projectRoot.Replace('\','\\')
$importCode = "import sys; sys.path.insert(0, r'$rootEscaped'); import src.pipeline.song_project_engine; print('Source import: OK')"
& $python -c $importCode
if ($LASTEXITCODE -ne 0) { throw 'Phoenix source import failed.' }

Write-Host '[Phoenix] Preparing reference song...' -ForegroundColor Cyan
$audioFull = (Resolve-Path $AudioPath).Path
$audioEscaped = $audioFull.Replace('\','\\')
$projectEscaped = $ProjectName.Replace("'", "''")
$artistEscaped = $ArtistName.Replace("'", "''")
$code = @"
import json
import sys
from pathlib import Path
root = Path(r'$rootEscaped')
audio = Path(r'$audioEscaped')
sys.path.insert(0, str(root))
from src.pipeline.song_project_engine import SongProjectEngine
engine = SongProjectEngine(root / 'Projects')
manifest = engine.prepare(audio, '$projectEscaped', '$artistEscaped')
print(json.dumps(manifest, ensure_ascii=False, indent=2))
"@
& $python -c $code
if ($LASTEXITCODE -ne 0) { throw 'Reference preparation failed.' }

Write-Host '[Phoenix] Reference project prepared.' -ForegroundColor Green
