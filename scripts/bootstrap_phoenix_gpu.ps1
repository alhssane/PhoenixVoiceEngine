$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$python = 'C:\Users\alhss\AppData\Local\Programs\Python\Python310\python.exe'
$envPath = Join-Path $projectRoot '.venv_phoenix_gpu'

if (-not (Test-Path $python)) {
    throw "Python 3.10 was not found at $python"
}

Write-Host "[Phoenix] Creating isolated GPU environment: $envPath" -ForegroundColor Cyan
if (-not (Test-Path (Join-Path $envPath 'Scripts\python.exe'))) {
    & $python -m venv $envPath
}

$venvPython = Join-Path $envPath 'Scripts\python.exe'
$venvPip = Join-Path $envPath 'Scripts\pip.exe'

& $venvPython -m pip install --upgrade pip setuptools wheel

Write-Host "[Phoenix] Installing CUDA-enabled PyTorch 2.6.0 (CUDA 12.6 wheel)" -ForegroundColor Cyan
& $venvPip install --index-url https://download.pytorch.org/whl/cu126 `
    'torch==2.6.0' 'torchvision==0.21.0' 'torchaudio==2.6.0'

Write-Host "[Phoenix] Verifying CUDA" -ForegroundColor Cyan
& $venvPython -c "import torch; print('Torch:',torch.__version__); print('CUDA available:',torch.cuda.is_available()); print('CUDA runtime:',torch.version.cuda); print('GPU:',torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NONE'); print('VRAM_GB:',round(torch.cuda.get_device_properties(0).total_memory/1024**3,2) if torch.cuda.is_available() else 0)"

if ($LASTEXITCODE -ne 0) {
    throw 'PyTorch/CUDA verification failed.'
}

Write-Host "[Phoenix] GPU environment ready." -ForegroundColor Green
Write-Host "Activate with: .\.venv_phoenix_gpu\Scripts\Activate.ps1" -ForegroundColor Yellow
