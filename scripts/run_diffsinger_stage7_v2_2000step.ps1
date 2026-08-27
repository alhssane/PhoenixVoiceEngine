param(
    [Parameter(Mandatory=$false)][string]$DiffSinger = 'D:\PhoenixVoiceEngine\external\DiffSinger-openvpi',
    [Parameter(Mandatory=$false)][string]$Config = 'D:\PhoenixVoiceEngine\jobs\freed_joud_fixed_v2\phoenix_arabic_acoustic.yaml',
    [Parameter(Mandatory=$false)][string]$Binary = 'D:\PhoenixVoiceEngine\jobs\freed_joud_fixed_v2\datasets\binary_full_v4',
    [Parameter(Mandatory=$false)][string]$ExpName = 'phoenix_freed_joud_fixed_v2_train_2000step'
)

$ErrorActionPreference = 'Stop'
$python = 'D:\PhoenixVoiceEngine\.venv_phoenix_svs\Scripts\python.exe'
$preflight = Join-Path $PSScriptRoot 'stage7_diffusion_smoke.py'
$train = Join-Path $DiffSinger 'scripts\train.py'

foreach ($p in @($python, $preflight, $train, $Config, $Binary)) {
    if (-not (Test-Path $p)) { throw "Required path not found: $p" }
}

Write-Host '[Phoenix] Stage7-V2-2000: validating canonical binary dataset...' -ForegroundColor Cyan
& $python $preflight --diffsinger $DiffSinger --config $Config --binary $Binary
if ($LASTEXITCODE -ne 0) { throw 'Stage7-V2-2000 binary preflight failed.' }

$oldPwd = Get-Location
$oldPyPath = $env:PYTHONPATH
$oldCudnn = $env:TORCH_CUDNN_V8_API_ENABLED
try {
    Set-Location $DiffSinger
    $env:PYTHONPATH = $DiffSinger
    $env:TORCH_CUDNN_V8_API_ENABLED = '1'

    Write-Host "[Phoenix] Stage7-V2-2000: starting fresh 2000-step training on $ExpName..." -ForegroundColor Cyan
    & $python $train `
        --config $Config `
        --exp_name $ExpName `
        --reset `
        --hparams "max_updates=2000,max_batch_frames=8000,max_batch_size=1,max_val_batch_frames=8000,max_val_batch_size=1,val_check_interval=100,num_sanity_val_steps=1,log_interval=25,ds_workers=1,dataloader_prefetch_factor=2,permanent_ckpt_start=999999,permanent_ckpt_interval=999999,val_with_vocoder=False"
    if ($LASTEXITCODE -ne 0) { throw 'Stage7-V2-2000 training failed.' }
}
finally {
    Set-Location $oldPwd
    $env:PYTHONPATH = $oldPyPath
    $env:TORCH_CUDNN_V8_API_ENABLED = $oldCudnn
}

$work = Join-Path $DiffSinger "checkpoints\$ExpName"
if (-not (Test-Path $work)) { throw "Training completed but checkpoint work directory was not found: $work" }

Write-Host "[Phoenix] Stage7-V2-2000 completed. Experiment: $work" -ForegroundColor Green
