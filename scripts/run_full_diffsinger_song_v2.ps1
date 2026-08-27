param(
    [Parameter(Mandatory=$true)][string]$SourceWav,
    [Parameter(Mandatory=$false)][string]$WordsJson = '',
    [Parameter(Mandatory=$false)][string]$SongId = 'song_full',
    [Parameter(Mandatory=$false)][string]$ProjectRoot = 'D:\PhoenixVoiceEngine',
    [Parameter(Mandatory=$false)][string]$DiffSinger = 'D:\PhoenixVoiceEngine\external\DiffSinger-openvpi'
)

$ErrorActionPreference = 'Stop'
$python = Join-Path $ProjectRoot '.venv_phoenix_svs\Scripts\python.exe'
$scripts = Join-Path $ProjectRoot 'scripts'
foreach ($p in @($python, $SourceWav, $DiffSinger)) {
    if (-not (Test-Path $p)) { throw "Required path not found: $p" }
}

$jobRoot = Join-Path $ProjectRoot "jobs\$SongId"
$datasets = Join-Path $jobRoot 'datasets'
$reports = Join-Path $jobRoot 'reports'
$transcriptDir = Join-Path $jobRoot 'transcript'
New-Item -ItemType Directory -Force -Path $datasets,$reports,$transcriptDir | Out-Null

$duration = [double](& $python -c "import soundfile as sf,sys; print(sf.info(sys.argv[1]).duration)" $SourceWav)
if ($LASTEXITCODE -ne 0) { throw 'Audio duration preflight failed.' }

if ([string]::IsNullOrWhiteSpace($WordsJson)) {
    $rawWords = Join-Path $transcriptDir 'gemini_words.json'
    $geminiReport = Join-Path $transcriptDir 'gemini_transcript.json'
    $geminiRaw = Join-Path $transcriptDir 'gemini_raw.json'
    Write-Host '[Phoenix] No WordsJson supplied: automatic Gemini transcription...' -ForegroundColor Cyan
    & $python (Join-Path $scripts 'transcribe_song_gemini.py') --source-wav $SourceWav --output $geminiReport --words-output $rawWords --raw-output $geminiRaw --language ar-EG
    if ($LASTEXITCODE -ne 0) { throw 'Gemini transcription failed.' }
    $WordsJson = $rawWords
}

$canonicalWords = Join-Path $transcriptDir 'canonical_words.json'
Write-Host '[Phoenix] Canonicalizing transcript...' -ForegroundColor Cyan
& $python (Join-Path $scripts 'canonicalize_training_transcript.py') --input $WordsJson --output $canonicalWords
if ($LASTEXITCODE -ne 0) { throw 'Canonical transcript failed.' }

$validation = Join-Path $reports 'transcript_validation.json'
& $python (Join-Path $scripts 'validate_training_transcript.py') --words-json $canonicalWords --audio-duration $duration --repair-mojibake --output $validation
if ($LASTEXITCODE -ne 0) { throw 'Transcript validation failed.' }

$coverage = Join-Path $reports 'transcript_coverage_audit.json'
& $python (Join-Path $scripts 'audit_transcript_coverage.py') --source-wav $SourceWav --words-json $canonicalWords --output $coverage
if ($LASTEXITCODE -ne 0) { throw 'Transcript coverage failed.' }

$stage1 = Join-Path $datasets 'stage1_full_v4'
$stage3 = Join-Path $datasets 'stage3_full_v4'
$stage4 = Join-Path $datasets 'stage4_ar_full_v4'
$stage5 = Join-Path $datasets 'stage5_full_v4'
$binary = Join-Path $datasets 'binary_full_v4'
$config = Join-Path $jobRoot 'phoenix_arabic_acoustic.yaml'

Write-Host '[Phoenix] Stage1: canonical word-safe segmentation...' -ForegroundColor Cyan
& $python (Join-Path $scripts 'build_full_stage1_v3_word_safe.py') --source-wav $SourceWav --words-json $canonicalWords --output $stage1
if ($LASTEXITCODE -ne 0) { throw 'Stage1 failed.' }

Write-Host '[Phoenix] Stage3-v2: canonical Arabic forced alignment + F0...' -ForegroundColor Cyan
& $python (Join-Path $scripts 'build_diffsinger_dataset_stage3_v2.py') --stage1 $stage1 --output $stage3
if ($LASTEXITCODE -ne 0) { throw 'Stage3-v2 failed.' }

Write-Host '[Phoenix] Stage4-v2: canonical Arabic phone-set...' -ForegroundColor Cyan
& $python (Join-Path $scripts 'build_diffsinger_dataset_stage4_ar_v2.py') --stage1 $stage1 --stage3 $stage3 --output $stage4
if ($LASTEXITCODE -ne 0) { throw 'Stage4-v2 failed.' }

Write-Host '[Phoenix] Stage5: raw dataset validation/bake...' -ForegroundColor Cyan
& $python (Join-Path $scripts 'build_diffsinger_dataset_stage5.py') --stage4 $stage4 --output $stage5
if ($LASTEXITCODE -ne 0) { throw 'Stage5 failed.' }

Write-Host '[Phoenix] Stage6-v2: generic song config...' -ForegroundColor Cyan
& $python (Join-Path $scripts 'prepare_diffsinger_stage6_v2.py') --raw $stage5 --diffsinger $DiffSinger --config $config --binary $binary --speaker $SongId --language ar
if ($LASTEXITCODE -ne 0) { throw 'Stage6-v2 failed.' }

$oldPwd = Get-Location
$oldPy = $env:PYTHONPATH
try {
    Set-Location $DiffSinger
    $env:PYTHONPATH = $DiffSinger
    Write-Host '[Phoenix] Binarize...' -ForegroundColor Cyan
    & $python 'scripts\binarize.py' --config $config --exp_name ("phoenix_$SongId") --reset
    if ($LASTEXITCODE -ne 0) { throw 'Binarize failed.' }
}
finally {
    Set-Location $oldPwd
    $env:PYTHONPATH = $oldPy
}

$integrity = Join-Path $scripts 'stage7_diffusion_smoke.py'
Write-Host '[Phoenix] Final binary integrity gate...' -ForegroundColor Cyan
& $python $integrity --diffsinger $DiffSinger --config $config --binary $binary
if ($LASTEXITCODE -ne 0) { throw 'Binary integrity gate failed.' }

$manifest = [ordered]@{
    song_id = $SongId
    source_wav = (Resolve-Path $SourceWav).Path
    words_json = (Resolve-Path $canonicalWords).Path
    source_duration_sec = $duration
    stage1 = $stage1
    stage3 = $stage3
    stage4 = $stage4
    stage5 = $stage5
    config = $config
    binary = $binary
    transcript_validation = $validation
    transcript_coverage_audit = $coverage
    phoneme_contract = 'src/arabic/phoneme_contract.py'
    status = 'DATASET_READY_FOR_TRAINING'
    training_started = $false
}
$manifest | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $reports 'pipeline_manifest_v2.json') -Encoding UTF8
Write-Host "[Phoenix] DATASET_READY_FOR_TRAINING_V2: $SongId" -ForegroundColor Green
Write-Host "[Phoenix] Manifest: $(Join-Path $reports 'pipeline_manifest_v2.json')" -ForegroundColor Green
Write-Host '[Phoenix] Training was intentionally NOT started.' -ForegroundColor Yellow
