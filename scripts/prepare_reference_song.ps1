$ErrorActionPreference = 'Stop'

param(
    [Parameter(Mandatory=$true)][string]$AudioPath,
    [Parameter(Mandatory=$false)][string]$ProjectName = 'freed_joud_reference',
    [Parameter(Mandatory=$false)][string]$ArtistName = 'freed_joud'
)

$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot '.venv_phoenix_gpu\Scripts\python.exe'
$requirements = Join-Path $projectRoot 'requirements\requirements.txt'
$branch = 'foundation-hardening'
$rawBase = "https://raw.githubusercontent.com/alhssane/PhoenixVoiceEngine/$branch"

if (-not (Test-Path $python)) { throw "Phoenix GPU Python not found: $python" }
if (-not (Test-Path $AudioPath)) { throw "Audio file not found: $AudioPath" }

# Sync the orchestration layer into the working copy without touching unrelated local files.
$requiredFiles = @(
    'src/pipeline/song_project_engine.py',
    'src/synthesis/synthesis_backend.py',
    'src/synthesis/hybrid_singing_backend.py',
    'src/project/project_manager.py',
    'src/transcription/full_song_transcription_engine.py',
    'src/trainer/artist_training_engine.py',
    'src/analysis/clean_vocal_signature_engine.py',
    'src/analysis/real_note_extraction_engine.py',
    'src/analysis/syllable_detection_engine.py'
)

foreach ($relativePath in $requiredFiles) {
    $destination = Join-Path $projectRoot ($relativePath -replace '/', '\\')
    $destinationDir = Split-Path -Parent $destination
    if (-not (Test-Path $destinationDir)) {
        New-Item -ItemType Directory -Path $destinationDir -Force | Out-Null
    }

    $uri = "$rawBase/$relativePath"
    Write-Host "[Phoenix] Syncing $relativePath" -ForegroundColor DarkCyan
    Invoke-WebRequest -Uri $uri -OutFile $destination
}

Write-Host '[Phoenix] Installing/validating Phoenix runtime dependencies...' -ForegroundColor Cyan
& $python -m pip install -r $requirements
if ($LASTEXITCODE -ne 0) { throw 'Phoenix runtime dependency installation failed.' }

Write-Host '[Phoenix] Preparing reference song...' -ForegroundColor Cyan
$code = @'
import json
import sys
from pathlib import Path

root = Path(r'''__ROOT__''')
audio = Path(r'''__AUDIO__''')
project_name = r'''__PROJECT__'''
artist_name = r'''__ARTIST__'''

sys.path.insert(0, str(root))

from src.pipeline.song_project_engine import SongProjectEngine

engine = SongProjectEngine(root / 'Projects')
manifest = engine.prepare(audio, project_name, artist_name)
print(json.dumps(manifest, ensure_ascii=False, indent=2))
'@
$code = $code.Replace('__ROOT__', $projectRoot.Replace('\','\\'))
$code = $code.Replace('__AUDIO__', (Resolve-Path $AudioPath).Path.Replace('\','\\'))
$code = $code.Replace('__PROJECT__', $ProjectName.Replace("'", "''"))
$code = $code.Replace('__ARTIST__', $ArtistName.Replace("'", "''"))

& $python -c $code
if ($LASTEXITCODE -ne 0) { throw 'Reference preparation failed.' }

Write-Host '[Phoenix] Reference project prepared.' -ForegroundColor Green
Write-Host ("Project root: " + (Join-Path $projectRoot ('Projects\' + $ArtistName + ' - ' + $ProjectName))) -ForegroundColor Yellow
