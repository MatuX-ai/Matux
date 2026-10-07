# Clean-port-9222.ps1
# 清理 9222 端口 + SingletonLock

$port = 9222
Write-Host "[1/3] Killing processes on port $port ..."
$conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
if ($conns) {
  foreach ($c in $conns) {
    $pid = $c.OwningProcess
    try {
      Stop-Process -Id $pid -Force -ErrorAction Stop
      Write-Host ("  Killed PID {0}" -f $pid)
    } catch {
      Write-Host ("  Skip PID {0}: {1}" -f $pid, $_.Exception.Message)
    }
  }
} else {
  Write-Host "  (port $port free)"
}

Write-Host "[2/3] Removing SingletonLock files ..."
$paths = @(
  "$env:APPDATA\imato\Singleton*",
  "$env:LOCALAPPDATA\imato\Singleton*"
)
$any = $false
foreach ($p in $paths) {
  if (Test-Path $p) {
    Remove-Item $p -Force -ErrorAction SilentlyContinue
    Write-Host "  Removed $p"
    $any = $true
  }
}
if (-not $any) { Write-Host "  (no SingletonLock found)" }

Write-Host "[3/3] Verifying port $port is free ..."
$remain = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
if ($remain) {
  Write-Host "  WARNING: port $port still has listeners:"
  $remain | Select-Object LocalPort, OwningProcess | Format-Table | Out-String | Write-Host
  exit 1
} else {
  Write-Host ("  port {0} is free [OK]" -f $port)
  exit 0
}
