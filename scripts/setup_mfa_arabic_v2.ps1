$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$miniforge = Join-Path $projectRoot 'miniforge3'
$conda = Join-Path $miniforge 'Scripts\conda.exe'
$envName = 'phoenix_mfa_arabic'
$envPath = Join-Path $projectRoot 'mfa_arabic'

if (-not (Test-Path $conda)) { throw "Conda executable not found: $conda" }

Write-Host '[Phoenix] Creating/verifying dedicated MFA Arabic environment...' -ForegroundColor Cyan
& $conda env list | Out-Host

$envExists = Test-Path (Join-Path $envPath 'python.exe')
if (-not $envExists) {
    & $conda create -p $envPath python=3.8 -y
    if ($LASTEXITCODE -ne 0) { throw 'Failed to create MFA Python 3.8 environment.' }
}

$python = Join-Path $envPath 'python.exe'
Write-Host '[Phoenix] Installing Montreal Forced Aligner 2.0.6...' -ForegroundColor Cyan
& $python -m pip install --upgrade pip
& $python -m pip install 'montreal-forced-aligner==2.0.6'
if ($LASTEXITCODE -ne 0) { throw 'Failed to install Montreal Forced Aligner 2.0.6.' }

Write-Host '[Phoenix] Downloading Arabic MFA dictionary/model...' -ForegroundColor Cyan
& $python -m montreal_forced_aligner.command_line model download dictionary arabic_mfa
if ($LASTEXITCODE -ne 0) { throw 'Failed to download Arabic MFA dictionary.' }
& $python -m montreal_forced_aligner.command_line model download acoustic arabic_mfa
if ($LASTEXITCODE -ne 0) { throw 'Failed to download Arabic MFA acoustic model.' }

Write-Host '[Phoenix] Validating MFA installation...' -ForegroundColor Cyan
& $python -c "import montreal_forced_aligner as mfa; print('MFA:', mfa.__version__)"
if ($LASTEXITCODE -ne 0) { throw 'MFA import validation failed.' }

Write-Host '[Phoenix] Arabic MFA environment ready.' -ForegroundColor Green
Write-Host ('Python: ' + $python) -ForegroundColor Yellow
Write-Host ('Environment: ' + $envPath) -ForegroundColor Yellow
