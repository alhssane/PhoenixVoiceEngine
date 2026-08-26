$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$env = Join-Path $root 'mfa_arabic'
$miniforge = Join-Path $root 'miniforge3\Scripts\conda.exe'

if (-not (Test-Path $miniforge)) { throw "Miniforge conda not found: $miniforge" }

Write-Host '[Phoenix] Creating dedicated MFA Python 3.8 environment...' -ForegroundColor Cyan
& $miniforge create -p $env python=3.8 -y
if ($LASTEXITCODE -ne 0) { throw 'Failed to create MFA environment.' }

$python = Join-Path $env 'python.exe'
if (-not (Test-Path $python)) { throw "MFA Python not found after environment creation: $python" }

Write-Host '[Phoenix] Installing Montreal Forced Aligner 2.0.6...' -ForegroundColor Cyan
& $python -m pip install --upgrade pip
& $python -m pip install 'montreal-forced-aligner==2.0.6'
if ($LASTEXITCODE -ne 0) { throw 'MFA installation failed.' }

Write-Host '[Phoenix] Verifying MFA installation...' -ForegroundColor Cyan
& $python -c "import sys; import montreal_forced_aligner as m; print('Python:',sys.version); print('MFA import: OK'); print('MFA path:',m.__file__)"
if ($LASTEXITCODE -ne 0) { throw 'MFA verification failed.' }

Write-Host '[Phoenix] MFA Arabic environment ready.' -ForegroundColor Green
Write-Host ("Python: " + $python)
Write-Host 'Next: build Arabic MFA corpus and obtain dictionary/acoustic model.' -ForegroundColor Yellow
