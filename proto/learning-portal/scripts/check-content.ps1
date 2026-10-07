$routes = @('/', '/login', '/register', '/web', '/mobile')
foreach ($r in $routes) {
  try {
    $resp = Invoke-WebRequest -Uri "http://localhost:3000$r" -UseBasicParsing -TimeoutSec 30
    $len = $resp.Content.Length
    $hasError = $resp.Content -match 'Application error|Internal Server Error|Failed to compile'
    Write-Host "$r -> $($resp.StatusCode), length=$len, error=$hasError"
  } catch {
    Write-Host "$r -> ERROR: $($_.Exception.Message)"
  }
}
