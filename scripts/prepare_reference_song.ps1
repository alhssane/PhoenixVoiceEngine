$ErrorActionPreference = 'Stop'

param(
    [Parameter(Mandatory=$true)][string]$AudioPath,
    [Parameter(Mandatory=$false)][string]$ProjectName = 'freed_joud_reference',
    [Parameter(Mandatory=$false)][string]$ArtistName = 'freed_joud'
)

$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot '.venv_phoenix_gpu\Scripts\python.exe'
$requirements = Join-Path $projectRoot 'requirements\requirements.txt'

if (-not (Test-Path $python)) { throw "Phoenix GPU Python not found: $python" }
if (-not (Test-Path $AudioPath)) { throw "Audio file not found: $AudioPath" }

# The working copy may lag behind the GitHub foundation branch. Pull only the
# small orchestration files required by this script instead of changing the
# user's whole checkout or local changes.
$requiredFiles = @(
    'src/pipeline/song_project_engine.py',
    'src/synthesis/synthesis_backend.py',
    'src/synthesis/hybrid_singing_backend.py'
)
foreach ($relativePath in $requiredFiles) {
    $destination = Join-Path $projectRoot ($relativePath -replace '/', '\\')
    $destinationDir = Split-Path -Parent $destination
    if (-not (Test-Path $destinationDir)) { New-Item -ItemType Directory -Path $destinationDir -Force | Out-Null }
    if (-not (Test-Path $destination)) {
        $uri = "https://raw.githubusercontent.com/alhssane/PhoenixVoiceEngine/foundation-hardening/$relativePath"
        Write-Host "[Phoenix] Fetching missing project file: $relativePath" -ForegroundColor DarkCyan
        Invoke-WebRequest -Uri $uri -OutFile $destination
    }
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

# Guarantee that the repository root is importable regardless of the caller's cwd.
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
