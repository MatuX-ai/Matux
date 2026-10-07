$routes = @('/', '/login', '/register', '/web', '/mobile')
$results = @()
foreach ($r in $routes) {
  try {
    $resp = Invoke-WebRequest -Uri "http://localhost:3000$r" -UseBasicParsing -TimeoutSec 30
    $results += [PSCustomObject]@{ Route = $r; Status = $resp.StatusCode; OK = ($resp.StatusCode -eq 200) }
  } catch {
    $code = $_.Exception.Response.StatusCode.value__
    $results += [PSCustomObject]@{ Route = $r; Status = $code; OK = $false }
  }
}
$results | Format-Table -AutoSize
$failed = $results | Where-Object { -not $_.OK }
if ($failed) { Write-Host "FAILED: $($failed.Count) route(s)"; exit 1 } else { Write-Host "ALL PASS"; exit 0 }
