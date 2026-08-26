param(
    [Parameter(Mandatory=$false)][string]$DiffSinger = 'D:\PhoenixVoiceEngine\external\DiffSinger-openvpi',
    [Parameter(Mandatory=$false)][string]$Config = 'D:\PhoenixVoiceEngine\configs\diffsinger\phoenix_arabic_acoustic.yaml',
    [Parameter(Mandatory=$false)][string]$Binary = 'D:\PhoenixVoiceEngine\datasets\freed_joud_diffsinger_binary'
)

$python = 'D:\PhoenixVoiceEngine\.venv_phoenix_svs\Scripts\python.exe'
$preflight = Join-Path $PSScriptRoot 'stage7_diffusion_smoke.py'
$train = Join-Path $DiffSinger 'scripts\train.py'

if (-not (Test-Path $python)) { throw "Phoenix SVS Python not found: $python" }
if (-not (Test-Path $preflight)) { throw "Stage7 preflight not found: $preflight" }
if (-not (Test-Path $train)) { throw "DiffSinger train.py not found: $train" }

Write-Host '[Phoenix] Stage9-1000: validating binary Dataset integrity...' -ForegroundColor Cyan
& $python $preflight --diffsinger $DiffSinger --config $Config --binary $Binary
if ($LASTEXITCODE -ne 0) { throw 'Stage9 binary preflight failed.' }

$oldPwd = Get-Location
$oldPyPath = $env:PYTHONPATH
$oldCudnn = $env:TORCH_CUDNN_V8_API_ENABLED
try {
    Set-Location $DiffSinger
    $env:PYTHONPATH = $DiffSinger
    $env:TORCH_CUDNN_V8_API_ENABLED = '1'

    $expName = 'phoenix_freed_joud_stage9_1000step'
    Write-Host '[Phoenix] Stage9-1000: starting 1000-step DiffSinger training...' -ForegroundColor Cyan
    & $python $train `
        --config $Config `
        --exp_name $expName `
        --reset `
        --hparams "max_updates=1000,max_batch_frames=8000,max_batch_size=1,max_val_batch_frames=8000,max_val_batch_size=1,val_check_interval=25,num_sanity_val_steps=1,log_interval=25,ds_workers=1,dataloader_prefetch_factor=2,num_ckpt_keep=8,permanent_ckpt_start=999999,permanent_ckpt_interval=999999,val_with_vocoder=False"
    if ($LASTEXITCODE -ne 0) { throw 'Stage9 1000-step training failed.' }
}
finally {
    Set-Location $oldPwd
    $env:PYTHONPATH = $oldPyPath
    $env:TORCH_CUDNN_V8_API_ENABLED = $oldCudnn
}

$work = Join-Path $DiffSinger "checkpoints\phoenix_freed_joud_stage9_1000step"
if (-not (Test-Path $work)) { throw "Training completed but checkpoint work directory was not found: $work" }

Write-Host "[Phoenix] Stage9-1000 completed. Experiment: $work" -ForegroundColor Green
