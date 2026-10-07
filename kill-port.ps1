$p = Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue
if ($p) {
    $pid = $p[0].OwningProcess
    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    Write-Host "Killed PID:" $pid
} else {
    Write-Host "No process on 8001"
}
