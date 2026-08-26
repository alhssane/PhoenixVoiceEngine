$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot '.venv_phoenix_gpu\Scripts\python.exe'
$svsRoot = Join-Path $projectRoot 'external\DiffSinger-openvpi'
$svsEnv = Join-Path $projectRoot '.venv_phoenix_svs'

if (-not (Test-Path $python)) {
    throw "Phoenix GPU Python not found: $python"
}

if (-not (Test-Path $svsRoot)) {
    Write-Host '[Phoenix] Cloning OpenVPI DiffSinger...' -ForegroundColor Cyan
    git clone https://github.com/SleePerwtm/DiffSinger-openvpi.git $svsRoot
}

$basePython = 'C:\Users\alhss\AppData\Local\Programs\Python\Python310\python.exe'
if (-not (Test-Path $basePython)) {
    throw "Python 3.10 not found: $basePython"
}

if (-not (Test-Path (Join-Path $svsEnv 'Scripts\python.exe'))) {
    Write-Host "[Phoenix] Creating SVS environment: $svsEnv" -ForegroundColor Cyan
    & $basePython -m venv $svsEnv
}

$envPython = Join-Path $svsEnv 'Scripts\python.exe'
$envPip = Join-Path $svsEnv 'Scripts\pip.exe'

& $envPython -m pip install --upgrade pip setuptools wheel

Write-Host '[Phoenix] Installing OpenVPI DiffSinger dependencies...' -ForegroundColor Cyan
& $envPip install -r (Join-Path $svsRoot 'requirements.txt')

Write-Host '[Phoenix] SVS environment check...' -ForegroundColor Cyan
& $envPython -c "import sys; print('Python:',sys.version); import torch; print('Torch:',torch.__version__); print('CUDA:',torch.cuda.is_available()); print('Runtime:',torch.version.cuda); print('GPU:',torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NONE')"

if ($LASTEXITCODE -ne 0) { throw 'SVS environment verification failed.' }

Write-Host '[Phoenix] OpenVPI DiffSinger environment ready.' -ForegroundColor Green
Write-Host "SVS source: $svsRoot" -ForegroundColor Yellow
