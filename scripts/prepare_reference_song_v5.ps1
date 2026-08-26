$ErrorActionPreference = 'Stop'

if ($args.Count -lt 1) {
    throw 'Usage: prepare_reference_song_v5.ps1 <AudioPath> [ProjectName] [ArtistName]'
}

$AudioPath = $args[0]
$ProjectName = if ($args.Count -ge 2) { $args[1] } else { 'freed_joud_reference' }
$ArtistName = if ($args.Count -ge 3) { $args[2] } else { 'freed_joud' }

$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot '.venv_phoenix_gpu\Scripts\python.exe'
$requirements = Join-Path $projectRoot 'requirements\requirements.txt'
$rawBase = 'https://raw.githubusercontent.com/alhssane/PhoenixVoiceEngine/foundation-hardening'

if (-not (Test-Path $python)) { throw "Phoenix GPU Python not found: $python" }
if (-not (Test-Path $AudioPath)) { throw "Audio file not found: $AudioPath" }

Write-Host '[Phoenix] Installing/validating runtime dependencies...' -ForegroundColor Cyan
& $python -m pip install -r $requirements
if ($LASTEXITCODE -ne 0) { throw 'Phoenix runtime dependency installation failed.' }
& $python -m pip install 'librosa>=0.10,<1' 'soundfile>=0.12,<1' 'faster-whisper>=1.1,<2'
if ($LASTEXITCODE -ne 0) { throw 'Core audio dependency installation failed.' }

Write-Host '[Phoenix] Verifying runtime imports...' -ForegroundColor Cyan
& $python -c "import librosa, soundfile, faster_whisper; print('Runtime imports: OK'); print('librosa:', librosa.__version__); print('soundfile:', soundfile.__version__)"
if ($LASTEXITCODE -ne 0) { throw 'Required runtime modules are unavailable.' }

Write-Host '[Phoenix] Synchronizing required orchestration files...' -ForegroundColor DarkCyan
$requiredFiles = @(
    'src\project\project_manager.py',
    'src\pipeline\song_project_engine.py'
)
foreach ($relativePath in $requiredFiles) {
    $destination = Join-Path $projectRoot $relativePath
    $destinationDir = Split-Path -Parent $destination
    New-Item -ItemType Directory -Path $destinationDir -Force | Out-Null
    $uri = "$rawBase/$($relativePath -replace '\\','/')?cache=phoenix-v5"
    Invoke-WebRequest -Uri $uri -OutFile $destination
    Write-Host "[Phoenix] Synced: $relativePath" -ForegroundColor DarkCyan
}

Write-Host '[Phoenix] Validating source import...' -ForegroundColor Cyan
$rootEscaped = $projectRoot.Replace('\','\\')
$importCode = "import sys; sys.path.insert(0, r'$rootEscaped'); import src.pipeline.song_project_engine; print('Source import: OK')"
& $python -c $importCode
if ($LASTEXITCODE -ne 0) { throw 'Phoenix source import failed.' }

Write-Host '[Phoenix] Preparing reference song...' -ForegroundColor Green
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
