param(
    [Parameter(Mandatory=$true)][string]$AudioPath,
    [Parameter(Mandatory=$false)][string]$ProjectName = 'freed_joud_reference',
    [Parameter(Mandatory=$false)][string]$ArtistName = 'freed_joud'
)

$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot '.venv_phoenix_gpu\Scripts\python.exe'
$requirements = Join-Path $projectRoot 'requirements\requirements.txt'

if (-not (Test-Path $python)) { throw "Phoenix GPU Python not found: $python" }
if (-not (Test-Path $AudioPath)) { throw "Audio file not found: $AudioPath" }

Write-Host '[Phoenix] Installing/validating Phoenix runtime dependencies...' -ForegroundColor Cyan
& $python -m pip install -r $requirements
if ($LASTEXITCODE -ne 0) { throw 'Phoenix runtime dependency installation failed.' }

Write-Host '[Phoenix] Preparing reference song...' -ForegroundColor Cyan
$code = @'
import json
from pathlib import Path
from src.pipeline.song_project_engine import SongProjectEngine

root = Path(r'''__ROOT__''')
audio = Path(r'''__AUDIO__''')
project_name = r'''__PROJECT__'''
artist_name = r'''__ARTIST__'''

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

$projectPath = Join-Path $projectRoot ('Projects\' + $ArtistName + ' - ' + $ProjectName)
Write-Host '[Phoenix] Reference project prepared.' -ForegroundColor Green
Write-Host ("Project root: " + $projectPath) -ForegroundColor Yellow
