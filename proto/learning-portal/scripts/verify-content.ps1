$checks = @(
  @{ Route = '/register'; Pattern = 'password|grade|nickname|grade' },
  @{ Route = '/web'; Pattern = 'profile-edit' },
  @{ Route = '/login'; Pattern = '/register' }
)
foreach ($c in $checks) {
  $resp = Invoke-WebRequest -Uri "http://localhost:3000$($c.Route)" -UseBasicParsing -TimeoutSec 30
  $found = $resp.Content -match $c.Pattern
  Write-Host "$($c.Route) -> pattern '$($c.Pattern)' found=$found"
}
