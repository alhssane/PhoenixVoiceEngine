param(
    [Parameter(Mandatory=$true)][string]$SourceWav,
    [Parameter(Mandatory=$true)][string]$WordsJson,
    [Parameter(Mandatory=$false)][string]$SongId = 'song_full',
    [Parameter(Mandatory=$false)][string]$ProjectRoot = 'D:\PhoenixVoiceEngine',
    [Parameter(Mandatory=$false)][string]$DiffSinger = 'D:\PhoenixVoiceEngine\external\DiffSinger-openvpi'
)

$ErrorActionPreference = 'Stop'

$python = Join-Path $ProjectRoot '.venv_phoenix_svs\Scripts\python.exe'
$scriptRoot = Join-Path $ProjectRoot 'scripts'
$configTemplate = Join-Path $ProjectRoot 'configs\diffsinger\phoenix_arabic_acoustic.yaml'

foreach ($p in @($python, $SourceWav, $WordsJson, $DiffSinger)) {
    if (-not (Test-Path $p)) { throw "Required path not found: $p" }
}

$jobRoot = Join-Path $ProjectRoot "jobs\$SongId"
$datasets = Join-Path $jobRoot 'datasets'
$reports = Join-Path $jobRoot 'reports'
New-Item -ItemType Directory -Force -Path $datasets,$reports | Out-Null

Write-Host "[Phoenix] Song Pipeline: $SongId" -ForegroundColor Cyan
Write-Host "[Phoenix] Source: $SourceWav"
Write-Host "[Phoenix] Lyrics: $WordsJson"

# Audio duration preflight.
$durationText = & $python -c "import soundfile as sf,sys; print(sf.info(sys.argv[1]).duration)" $SourceWav
if ($LASTEXITCODE -ne 0) { throw 'Audio duration preflight failed.' }
$duration = [double]$durationText

# Transcript safety gate. It rejects known contamination, zero-duration words,
# overlaps and malformed timing BEFORE any expensive dataset work starts.
$validator = Join-Path $scriptRoot 'validate_training_transcript.py'
$transcriptReport = Join-Path $reports 'transcript_validation.json'
& $python $validator --words-json $WordsJson --audio-duration $duration --repair-mojibake --output $transcriptReport
if ($LASTEXITCODE -ne 0) {
    throw "Transcript gate failed. See: $transcriptReport"
}

$stage1 = Join-Path $datasets 'stage1_full_v3'
$stage2 = Join-Path $datasets 'stage2_full_v3'
$stage3 = Join-Path $datasets 'stage3_full_v3'
$stage4 = Join-Path $datasets 'stage4_ar_full_v3'
$stage5 = Join-Path $datasets 'stage5_full_v3'
$binary = Join-Path $datasets 'binary_full_v3'
$config = Join-Path $jobRoot 'phoenix_arabic_acoustic.yaml'

Write-Host '[Phoenix] Stage1: FULL word-safe segmentation...' -ForegroundColor Cyan
& $python (Join-Path $scriptRoot 'build_full_stage1_v3_word_safe.py') `
    --source-wav $SourceWav `
    --words-json $WordsJson `
    --output $stage1
if ($LASTEXITCODE -ne 0) { throw 'Stage1 failed.' }

Write-Host '[Phoenix] Stage2: Arabic provisional phonemes + pitch...' -ForegroundColor Cyan
& $python (Join-Path $scriptRoot 'build_diffsinger_dataset_stage2.py') $stage1 $stage2
if ($LASTEXITCODE -ne 0) { throw 'Stage2 failed.' }

Write-Host '[Phoenix] Stage3: forced alignment...' -ForegroundColor Cyan
& $python (Join-Path $scriptRoot 'build_diffsinger_dataset_stage3.py') --stage1 $stage1 --stage2 $stage2 --output $stage3
if ($LASTEXITCODE -ne 0) { throw 'Stage3 failed.' }

Write-Host '[Phoenix] Stage4: Arabic phone-set...' -ForegroundColor Cyan
& $python (Join-Path $scriptRoot 'build_diffsinger_dataset_stage4_ar.py') --stage3 $stage3 --output $stage4
if ($LASTEXITCODE -ne 0) { throw 'Stage4 failed.' }

Write-Host '[Phoenix] Stage5: raw dataset validation/bake...' -ForegroundColor Cyan
& $python (Join-Path $scriptRoot 'build_diffsinger_dataset_stage5.py') --stage4 $stage4 --output $stage5
if ($LASTEXITCODE -ne 0) { throw 'Stage5 failed.' }

Write-Host '[Phoenix] Stage6: DiffSinger config...' -ForegroundColor Cyan
& $python (Join-Path $scriptRoot 'prepare_diffsinger_stage6.py') --raw $stage5 --diffsinger $DiffSinger --config $config --binary $binary
if ($LASTEXITCODE -ne 0) { throw 'Stage6 failed.' }

# Run binarization from the DiffSinger working directory so relative base configs resolve.
$oldPwd = Get-Location
$oldPyPath = $env:PYTHONPATH
try {
    Set-Location $DiffSinger
    $env:PYTHONPATH = $DiffSinger
    Write-Host '[Phoenix] Binarize...' -ForegroundColor Cyan
    & $python 'scripts\binarize.py' --config $config --exp_name ("phoenix_$SongId") --reset
    if ($LASTEXITCODE -ne 0) { throw 'Binarize failed.' }
}
finally {
    Set-Location $oldPwd
    $env:PYTHONPATH = $oldPyPath
}

# Final binary integrity gate; training is explicitly NOT started by this runner.
$preflight = Join-Path $scriptRoot 'stage7_diffusion_smoke.py'
Write-Host '[Phoenix] Final binary integrity gate...' -ForegroundColor Cyan
& $python $preflight --diffsinger $DiffSinger --config $config --binary $binary
if ($LASTEXITCODE -ne 0) { throw 'Binary integrity gate failed.' }

$manifest = [ordered]@{
    song_id = $SongId
    source_wav = (Resolve-Path $SourceWav).Path
    words_json = (Resolve-Path $WordsJson).Path
    source_duration_sec = $duration
    stage1 = $stage1
    stage2 = $stage2
    stage3 = $stage3
    stage4 = $stage4
    stage5 = $stage5
    config = $config
    binary = $binary
    status = 'DATASET_READY_FOR_TRAINING'
    training_started = $false
}
$manifest | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $reports 'pipeline_manifest.json') -Encoding UTF8

Write-Host "[Phoenix] DATASET_READY_FOR_TRAINING: $SongId" -ForegroundColor Green
Write-Host "[Phoenix] Pipeline manifest: $(Join-Path $reports 'pipeline_manifest.json')" -ForegroundColor Green
Write-Host '[Phoenix] Training was intentionally NOT started.' -ForegroundColor Yellow
