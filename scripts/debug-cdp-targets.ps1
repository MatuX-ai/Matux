# Start Electron, then probe /json targets, then leave Electron running
$env:BACKEND_PORT = '8000'
$env:PORT = '8000'
$env:NODE_ENV = 'production'

# Clean SingletonLock and 9222 port
Get-NetTCPConnection -LocalPort 9222 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 2
Remove-Item "$env:APPDATA\imato\Singleton*" -ErrorAction SilentlyContinue

$exe = 'g:\iMato\node_modules\electron\dist\electron.exe'
$electronDir = 'g:\iMato\electron'
$proc = Start-Process -FilePath $exe -ArgumentList @($electronDir, '--remote-debugging-port=9222', '--disable-gpu-sandbox') -PassThru -WindowStyle Hidden
Write-Host "Electron PID: $($proc.Id)"

Start-Sleep -Seconds 8
$json = Invoke-RestMethod -Uri 'http://localhost:9222/json' -TimeoutSec 5
Write-Host "=== /json targets ==="
$json | ConvertTo-Json -Depth 3

Write-Host "=== /json/version ==="
$version = Invoke-RestMethod -Uri 'http://localhost:9222/json/version' -TimeoutSec 5
$version | ConvertTo-Json -Depth 3

# Keep running for now
Write-Host "Leaving Electron running for further debugging"
