Write-Host "Starting build..." -ForegroundColor Green
$startTime = Get-Date

$errorFound = $false
$output = & ng build --configuration development --optimization=false 2>&1 | ForEach-Object {
    Write-Host $_
    if ($_ -match "ERROR" -or $_ -match "error TS" -or $_ -match "Failed to compile") {
        $errorFound = $true
    }
}

$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds

Write-Host "`n=========================" -ForegroundColor Cyan
Write-Host "Build completed!" -ForegroundColor Cyan
Write-Host "Duration: $($duration.ToString('0.00')) seconds" -ForegroundColor Cyan
Write-Host "=========================`n" -ForegroundColor Cyan

if ($LASTEXITCODE -eq 0 -and -not $errorFound) {
    Write-Host "SUCCESS: Build completed successfully!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "FAILED: Build encountered errors." -ForegroundColor Red
    exit 1
}
