$report = Get-Content eslint-report.json -Raw | ConvertFrom-Json
$errCount = @{}
$warnCount = @{}
foreach($f in $report) {
    foreach($m in $f.messages) {
        $rule = $m.ruleId
        if ($m.severity -eq 2) {
            if (-not $errCount.ContainsKey($rule)) { $errCount[$rule] = 0 }
            $errCount[$rule]++
        } elseif ($m.severity -eq 1) {
            if (-not $warnCount.ContainsKey($rule)) { $warnCount[$rule] = 0 }
            $warnCount[$rule]++
        }
    }
}
Write-Host "=== ERRORS ==="
$errCount.GetEnumerator() | Sort-Object Value -Descending | ForEach-Object { Write-Host "$($_.Name) : $($_.Value)" }
Write-Host "=== WARNINGS ==="
$warnCount.GetEnumerator() | Sort-Object Value -Descending | ForEach-Object { Write-Host "$($_.Name) : $($_.Value)" }
