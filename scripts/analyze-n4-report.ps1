# analyze-n4-report.ps1
# 解析最新 test-report-*.json，输出 passed/failed 列表

$r = Get-ChildItem 'g:\iMato\tests\test-results\auto-test\test-report-*.json' |
  Sort-Object LastWriteTime -Descending | Select-Object -First 1
Write-Host ("Reading: " + $r.FullName)
Write-Host ''

$json = Get-Content $r.FullName -Raw -Encoding UTF8
$obj = $json | ConvertFrom-Json

Write-Host ('SUMMARY: total={0} passed={1} failed={2} skipped={3} warnings={4}' -f `
  $obj.summary.total, $obj.summary.passed, $obj.summary.failed, $obj.summary.skipped, $obj.summary.warnings)
Write-Host ('Duration: {0}s' -f $obj.duration.totalSeconds)
Write-Host ''

Write-Host '=== FAILED PAGES ==='
$failed = $obj.pages | Where-Object { $_.status -eq 'failed' }
foreach ($p in $failed) {
  Write-Host ("  {0,-25} {1,-30}" -f $p.name, $p.path)
  Write-Host ("    error: " + $p.error)
  foreach ($c in $p.requiredChecks) {
    Write-Host ("    required: {0} = {1}" -f $c.description, $c.found)
  }
}
Write-Host ''

Write-Host '=== PASSED PAGES ==='
$passed = $obj.pages | Where-Object { $_.status -eq 'passed' }
foreach ($p in $passed) {
  $line = ("  {0,-25} {1,-30} {2}ms" -f $p.name, $p.path, $p.loadTimeMs)
  Write-Host $line
}
Write-Host ''

Write-Host '=== SKIPPED PAGES ==='
$skipped = $obj.pages | Where-Object { $_.status -eq 'skipped' }
foreach ($p in $skipped) {
  Write-Host ("  {0,-25} {1,-30}" -f $p.name, $p.path)
}
