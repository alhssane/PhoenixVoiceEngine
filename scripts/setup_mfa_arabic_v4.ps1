$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$miniforge = Join-Path $projectRoot 'miniforge3\condabin\conda.bat'
$envPath = Join-Path $projectRoot 'mfa_arabic'
$python = Join-Path $envPath 'python.exe'

if (-not (Test-Path $miniforge)) { throw "Miniforge conda.bat not found: $miniforge" }

Write-Host '[Phoenix] Creating/verifying dedicated MFA prefix environment...' -ForegroundColor Cyan
if (-not (Test-Path $python)) {
    & cmd.exe /c "`"$miniforge`" create --prefix `"$envPath`" python=3.8 -y"
    if ($LASTEXITCODE -ne 0) { throw 'Failed to create MFA Python environment.' }
}

if (-not (Test-Path $python)) { throw "MFA Python not found after environment creation: $python" }

Write-Host '[Phoenix] Verifying MFA Python...' -ForegroundColor Cyan
& $python --version
if ($LASTEXITCODE -ne 0) { throw 'MFA Python verification failed.' }

Write-Host '[Phoenix] Installing Montreal Forced Aligner 2.0.6...' -ForegroundColor Cyan
& $python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'pip upgrade failed.' }

& $miniforge install --prefix "$envPath" -c conda-forge montreal-forced-aligner=2.0.6 -y
if ($LASTEXITCODE -ne 0) { throw 'MFA 2.0.6 installation failed.' }

Write-Host '[Phoenix] Verifying MFA import...' -ForegroundColor Cyan
& $python -c "import montreal_forced_aligner as mfa; print('MFA import: OK'); print('MFA module:', mfa.__file__)"
if ($LASTEXITCODE -ne 0) { throw 'MFA import validation failed.' }

Write-Host '[Phoenix] MFA Arabic environment ready.' -ForegroundColor Green
Write-Host ("Python: " + $python) -ForegroundColor Yellow
Write-Host ("Environment: " + $envPath) -ForegroundColor Yellow
