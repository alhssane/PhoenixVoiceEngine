$ErrorActionPreference = 'Stop'
$root = 'D:\PhoenixVoiceEngine'
$python = Join-Path $root '.venv_phoenix_svs\Scripts\python.exe'
$script = Join-Path $root 'scripts\stage8_checkpoint_audit.py'
if (-not (Test-Path $python)) { throw "Phoenix SVS Python not found: $python" }
if (-not (Test-Path $script)) { throw "Stage8 script not found: $script" }
Write-Host '[Phoenix] Stage8: auditing local DiffSinger checkpoints...'
& $python $script --project $root
if ($LASTEXITCODE -ne 0) { throw 'Stage8 checkpoint audit failed.' }
Write-Host '[Phoenix] Stage8 audit completed.'
