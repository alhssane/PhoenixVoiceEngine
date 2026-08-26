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
$tempRoot = Join-Path $projectRoot '.cache\foundation_sync'
$zipPath = Join-Path $projectRoot '.cache\foundation-hardening.zip'

if (-not (Test-Path $python)) { throw "Phoenix GPU Python not found: $python" }
if (-not (Test-Path $AudioPath)) { throw "Audio file not found: $AudioPath" }

# Sync the source tree safely: only missing local files are copied from the
# foundation branch, so unrelated local edits are never overwritten.
if (-not (Test-Path (Join-Path $projectRoot 'src\pipeline\song_project_engine.py'))) {
    Write-Host '[Phoenix] Local source tree is behind foundation branch; syncing missing src files...' -ForegroundColor DarkCyan
    New-Item -ItemType Directory -Path (Split-Path $zipPath -Parent) -Force | Out-Null
    if (Test-Path $tempRoot) { Remove-Item $tempRoot -Recurse -Force }
    Invoke-WebRequest -Uri "https://github.com/alhssane/PhoenixVoiceEngine/archive/refs/heads/$branch.zip" -OutFile $zipPath
    Expand-Archive -Path $zipPath -DestinationPath $tempRoot -Force
    $extractedRoot = Get-ChildItem $tempRoot -Directory | Select-Object -First 1
    if (-not $extractedRoot) { throw 'Could not locate extracted foundation branch.' }

    $sourceSrc = Join-Path $extractedRoot.FullName 'src'
    $targetSrc = Join-Path $projectRoot 'src'
    if (-not (Test-Path $sourceSrc)) { throw 'Foundation branch does not contain src/.' }

    Get-ChildItem $sourceSrc -Recurse -File | ForEach-Object {
        $relative = $_.FullName.Substring($sourceSrc.Length).TrimStart('\','/')
        $destination = Join-Path $targetSrc $relative
        $destinationDir = Split-Path -Parent $destination
        if (-not (Test-Path $destination)) {
            New-Item -ItemType Directory -Path $destinationDir -Force | Out-Null
            Copy-Item $_.FullName $destination
            Write-Host "[Phoenix] Added missing source: src\$relative" -ForegroundColor DarkCyan
        }
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
