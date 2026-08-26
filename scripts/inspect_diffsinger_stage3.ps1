$ErrorActionPreference = 'Stop'

if ($args.Count -lt 1) { throw 'Usage: inspect_diffsinger_stage3.ps1 <Stage3Path>' }
$stage3 = (Resolve-Path $args[0]).Path
$report = Join-Path $stage3 'dataset_stage3.json'
if (-not (Test-Path $report)) { throw "Missing report: $report" }

$data = Get-Content $report -Raw | ConvertFrom-Json
Write-Host '[Phoenix] Stage3 diagnostics' -ForegroundColor Cyan
Write-Host ("Status: " + $data.status)
Write-Host ("Segments: " + $data.segment_count)
Write-Host ("Aligned: " + $data.aligned_count)
Write-Host ''

$failed = @($data.diagnostics | Where-Object { $_.status -ne 'ALIGNED' })
if ($failed.Count -eq 0) {
    Write-Host '[Phoenix] No failed segments.' -ForegroundColor Green
    exit 0
}

Write-Host ("Failed segments: " + $failed.Count) -ForegroundColor Yellow
foreach ($item in $failed) {
    Write-Host ("- " + $item.name + ' :: ' + $item.status) -ForegroundColor Red
    if ($null -ne $item.error) { Write-Host ("  error: " + $item.error) }
    if ($null -ne $item.coverage) { Write-Host ("  coverage: " + $item.coverage) }
    if ($null -ne $item.missing) { Write-Host ("  missing: " + (($item.missing -join ', '))) }
}
