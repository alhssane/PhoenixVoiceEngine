param(
    [Parameter(Mandatory=$true)][string]$SourceWav,
    [Parameter(Mandatory=$false)][string]$WordsJson = '',
    [Parameter(Mandatory=$false)][string]$SongId = 'song_full',
    [Parameter(Mandatory=$false)][string]$ProjectRoot = 'D:\PhoenixVoiceEngine',
    [Parameter(Mandatory=$false)][string]$DiffSinger = 'D:\PhoenixVoiceEngine\external\DiffSinger-openvpi'
)

$ErrorActionPreference = 'Stop'

$python = Join-Path $ProjectRoot '.venv_phoenix_svs\Scripts\python.exe'
$scriptRoot = Join-Path $ProjectRoot 'scripts'

foreach ($p in @($python, $SourceWav, $DiffSinger)) {
    if (-not (Test-Path $p)) { throw "Required path not found: $p" }
}

$jobRoot = Join-Path $ProjectRoot "jobs\$SongId"
$datasets = Join-Path $jobRoot 'datasets'
$reports = Join-Path $jobRoot 'reports'
$transcriptDir = Join-Path $jobRoot 'transcript'
New-Item -ItemType Directory -Force -Path $datasets,$reports,$transcriptDir | Out-Null

Write-Host "[Phoenix] Song Pipeline: $SongId" -ForegroundColor Cyan
Write-Host "[Phoenix] Source: $SourceWav"

# Audio duration preflight.
$durationText = & $python -c "import soundfile as sf,sys; print(sf.info(sys.argv[1]).duration)" $SourceWav
if ($LASTEXITCODE -ne 0) { throw 'Audio duration preflight failed.' }
$duration = [double]$durationText

# If lyrics/timing are not supplied, extract them automatically from the full
# song using Gemini 3.5 Transcribe with verbatim word-level timestamps.
$autoTranscribed = $false
if ([string]::IsNullOrWhiteSpace($WordsJson)) {
    $WordsJson = Join-Path $transcriptDir 'gemini_words.json'
    $geminiReport = Join-Path $transcriptDir 'gemini_transcript.json'
    $geminiRaw = Join-Path $transcriptDir 'gemini_raw.json'
    Write-Host '[Phoenix] No WordsJson supplied: automatic Gemini transcription...' -ForegroundColor Cyan
    & $python (Join-Path $scriptRoot 'transcribe_song_gemini.py') `
        --source-wav $SourceWav `
        --output $geminiReport `
        --words-output $WordsJson `
        --raw-output $geminiRaw `
        --language ar-EG
    if ($LASTEXITCODE -ne 0) { throw "Gemini transcription failed. See: $geminiReport" }
    $autoTranscribed = $true
}

if (-not (Test-Path $WordsJson)) { throw "WordsJson not found: $WordsJson" }

# Single source-of-truth transcript contract. Every downstream stage receives
# this canonical UTF-8 file. It repairs the legacy Arabic mojibake pattern
# before validation, segmentation, phonemization, alignment, or training.
$inputWordsJson = (Resolve-Path $WordsJson).Path
$canonicalWordsJson = Join-Path $transcriptDir 'canonical_words.json'
Write-Host "[Phoenix] Canonicalizing transcript: $inputWordsJson" -ForegroundColor Cyan
& $python (Join-Path $scriptRoot 'canonicalize_training_transcript.py') `
    --input $inputWordsJson `
    --output $canonicalWordsJson
if ($LASTEXITCODE -ne 0) { throw "Canonical transcript preparation failed: $canonicalWordsJson" }
$WordsJson = $canonicalWordsJson

Write-Host "[Phoenix] Lyrics/Timing (canonical): $WordsJson"

# Transcript safety gate. This catches known contamination, zero-duration
# words, overlaps and malformed timing before expensive dataset work starts.
$validator = Join-Path $scriptRoot 'validate_training_transcript.py'
$transcriptReport = Join-Path $reports 'transcript_validation.json'
& $python $validator --words-json $WordsJson --audio-duration $duration --repair-mojibake --output $transcriptReport
if ($LASTEXITCODE -ne 0) {
    throw "Transcript gate failed. See: $transcriptReport"
}

# Full-source coverage gate. This detects untimed regions that contain likely
# singing, preventing a Dataset that silently trains on only a small fraction
# of the supplied recording.
$coverageAudit = Join-Path $scriptRoot 'audit_transcript_coverage.py'
$coverageReport = Join-Path $reports 'transcript_coverage_audit.json'
& $python $coverageAudit --source-wav $SourceWav --words-json $WordsJson --output $coverageReport
if ($LASTEXITCODE -ne 0) {
    throw "Coverage gate failed: likely singing exists outside transcript timing. See: $coverageReport"
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

# Stage1 is a legacy preparation script. Normalize its emitted segment words
# from the same canonical transcript contract before any later stage consumes
# them, so a single mojibake bug cannot re-enter the pipeline here.
$stage1ManifestNormalizer = Join-Path $scriptRoot 'canonicalize_stage1_manifest.py'
& $python $stage1ManifestNormalizer `
    --stage1 $stage1 `
    --words-json $WordsJson
if ($LASTEXITCODE -ne 0) { throw 'Stage1 transcript contract enforcement failed.' }

# Stage2 in the current legacy preparation code discovers original_words.json
# through a fixed project glob. Keep exactly one compatibility mirror, copied
# from the canonical transcript, so glob ordering can never select stale text.
$stage2CompatRoot = Join-Path $jobRoot 'Projects'
if (Test-Path $stage2CompatRoot) {
    Remove-Item -LiteralPath $stage2CompatRoot -Recurse -Force
}
$stage2CompatWords = Join-Path $stage2CompatRoot 'auto_generated\lyrics\original_words.json'
New-Item -ItemType Directory -Force -Path (Split-Path $stage2CompatWords) | Out-Null
Copy-Item -LiteralPath $WordsJson -Destination $stage2CompatWords -Force
Write-Host "[Phoenix] Stage2 compatibility transcript: $stage2CompatWords" -ForegroundColor DarkCyan

Write-Host '[Phoenix] Stage2: Arabic provisional phonemes + pitch...' -ForegroundColor Cyan
& $python (Join-Path $scriptRoot 'build_diffsinger_dataset_stage2.py') $stage1 $stage2
if ($LASTEXITCODE -ne 0) { throw 'Stage2 failed.' }

Write-Host '[Phoenix] Stage3: forced alignment...' -ForegroundColor Cyan
& $python (Join-Path $scriptRoot 'build_diffsinger_dataset_stage3.py') --stage1 $stage1 --stage2 $stage2 --output $stage3
if ($LASTEXITCODE -ne 0) { throw 'Stage3 failed.' }

# Stage4 currently expects the legacy per-job Stage1 directory name when it
# resolves source WAVs. Create a junction alias to the real Stage1 output so
# no audio is duplicated and future jobs remain path-compatible.
$stage4CompatStage1 = Join-Path $datasets 'freed_joud_diffsinger_stage1_full_v3'
if (-not (Test-Path $stage4CompatStage1)) {
    New-Item -ItemType Junction -Path $stage4CompatStage1 -Target $stage1 | Out-Null
    Write-Host "[Phoenix] Stage4 compatibility junction: $stage4CompatStage1 -> $stage1" -ForegroundColor DarkCyan
}

Write-Host '[Phoenix] Stage4: Arabic phone-set...' -ForegroundColor Cyan
& $python (Join-Path $scriptRoot 'build_diffsinger_dataset_stage4_ar.py') --stage3 $stage3 --output $stage4
if ($LASTEXITCODE -ne 0) { throw 'Stage4 failed.' }

Write-Host '[Phoenix] Stage5: raw dataset validation/bake...' -ForegroundColor Cyan
& $python (Join-Path $scriptRoot 'build_diffsinger_dataset_stage5.py') --stage4 $stage4 --output $stage5
if ($LASTEXITCODE -ne 0) { throw 'Stage5 failed.' }

Write-Host '[Phoenix] Stage6: DiffSinger config...' -ForegroundColor Cyan
& $python (Join-Path $scriptRoot 'prepare_diffsinger_stage6.py') --raw $stage5 --diffsinger $DiffSinger --config $config --binary $binary
if ($LASTEXITCODE -ne 0) { throw 'Stage6 failed.' }

# Binarize from the DiffSinger working directory so relative base configs resolve.
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
    input_words_json = $inputWordsJson
    words_json = (Resolve-Path $WordsJson).Path
    canonical_words_json = (Resolve-Path $WordsJson).Path
    source_duration_sec = $duration
    auto_transcribed = $autoTranscribed
    stage2_compat_words = $stage2CompatWords
    stage4_compat_stage1 = $stage4CompatStage1
    stage1 = $stage1
    stage2 = $stage2
    stage3 = $stage3
    stage4 = $stage4
    stage5 = $stage5
    config = $config
    binary = $binary
    transcript_validation = $transcriptReport
    transcript_coverage_audit = $coverageReport
    status = 'DATASET_READY_FOR_TRAINING'
    training_started = $false
}
$manifest | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $reports 'pipeline_manifest.json') -Encoding UTF8

Write-Host "[Phoenix] DATASET_READY_FOR_TRAINING: $SongId" -ForegroundColor Green
Write-Host "[Phoenix] Pipeline manifest: $(Join-Path $reports 'pipeline_manifest.json')" -ForegroundColor Green
Write-Host '[Phoenix] Training was intentionally NOT started.' -ForegroundColor Yellow
