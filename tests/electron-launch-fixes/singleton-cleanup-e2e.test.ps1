# E2E test: simulate SingletonLock residue then launch Electron, verify auto-cleanup
# Outputs logs to g:\iMato\electron-e2e-singleton.log

$ErrorActionPreference = 'Stop'

$userData = Join-Path $env:APPDATA 'imato-desktop'
$logPath = 'g:\iMato\electron-e2e-singleton.log'
$electronExe = 'g:\iMato\electron\node_modules\electron\dist\electron.exe'
$electronDir = 'g:\iMato\electron'

# Clear previous log
"" | Out-File -FilePath $logPath -Encoding utf8

Write-Host "=== E2E Test: SingletonLock Residue Cleanup ==="
Write-Host "UserData: $userData"

# Step 1: Kill any running Electron
Write-Host "`n[Step 1] Killing any existing Electron process..."
Get-Process electron -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Milliseconds 500

# Step 2: Create fake SingletonLock residue
Write-Host "[Step 2] Creating fake SingletonLock residue..."
$lockFile = Join-Path $userData 'SingletonLock'
$symlinkFile = Join-Path $userData 'SingletonLockSymlink'
"fake-lock-from-prior-crash" | Out-File -FilePath $lockFile -Encoding utf8 -Force
"fake-symlink" | Out-File -FilePath $symlinkFile -Encoding utf8 -Force
Write-Host "  Created: $lockFile"
Write-Host "  Created: $symlinkFile"
$filesBefore = Get-ChildItem -Path $userData -Filter 'Singleton*' -Force | Select-Object -ExpandProperty Name
Write-Host "  Lock files before launch: $($filesBefore -join ', ')"

# Step 3: Launch Electron
Write-Host "`n[Step 3] Launching Electron..."
$env:BACKEND_PORT = '8002'
$env:NODE_ENV = 'development'
$proc = Start-Process -FilePath $electronExe -ArgumentList '.' -WorkingDirectory $electronDir -PassThru -NoNewWindow -RedirectStandardOutput $logPath -RedirectStandardError "$logPath.err"

Write-Host "  Electron PID: $($proc.Id)"

# Step 4: Wait and observe
Write-Host "`n[Step 4] Waiting 15s for Electron startup..."
Start-Sleep -Seconds 15

# Step 5: Check results
Write-Host "`n[Step 5] Checking results..."

# Check if Electron is still running
$alive = $false
try {
  $p = Get-Process -Id $proc.Id -ErrorAction Stop
  $alive = $true
  Write-Host "  Electron process status: RUNNING (PID $($p.Id))"
} catch {
  Write-Host "  Electron process status: EXITED"
}

# Check log for cleanup messages
$logContent = ""
if (Test-Path $logPath) {
  $logContent = Get-Content -Path $logPath -Raw -ErrorAction SilentlyContinue
}
if (Test-Path "$logPath.err") {
  $logContent += "`n" + (Get-Content -Path "$logPath.err" -Raw -ErrorAction SilentlyContinue)
}

$cleanupMsg = $logContent | Select-String -Pattern 'SingletonLock'
if ($cleanupMsg) {
  Write-Host "  Cleanup message in log: $($cleanupMsg[0].ToString().Trim())"
} else {
  Write-Host "  No cleanup message in log (maybe files were already gone)"
}

# Check if SingletonLock files were removed
$filesAfter = Get-ChildItem -Path $userData -Filter 'Singleton*' -Force -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name
Write-Host "  Lock files after launch: $(if ($filesAfter) { $filesAfter -join ', ' } else { '(none)' })"

# Final verdict
Write-Host "`n=== Verdict ==="
$pass = $true

if (-not $alive) {
  Write-Host "  FAIL: Electron process exited unexpectedly"
  $pass = $false
} else {
  Write-Host "  PASS: Electron is running"
}

# Either files removed OR cleanup message seen
$lockStillExists = ($filesAfter -contains 'SingletonLock') -or ($filesAfter -contains 'SingletonLockSymlink')
if ($lockStillExists -and -not $cleanupMsg) {
  Write-Host "  FAIL: SingletonLock residue not cleaned and no cleanup message"
  $pass = $false
} elseif (-not $lockStillExists) {
  Write-Host "  PASS: SingletonLock residue cleaned"
} else {
  Write-Host "  PASS: Cleanup message present (lock file handled)"
}

# Cleanup
Write-Host "`n[Cleanup] Stopping Electron..."
if ($alive) {
  Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
  Start-Sleep -Milliseconds 500
}
Remove-Item -Path $lockFile -Force -ErrorAction SilentlyContinue
Remove-Item -Path $symlinkFile -Force -ErrorAction SilentlyContinue
Remove-Item -Path "$logPath.err" -Force -ErrorAction SilentlyContinue

if ($pass) {
  Write-Host "`n=== E2E TEST PASSED ===" -ForegroundColor Green
  exit 0
} else {
  Write-Host "`n=== E2E TEST FAILED ===" -ForegroundColor Red
  Write-Host "Log content:"
  Write-Host "---"
  Write-Host $logContent.Substring(0, [Math]::Min(2000, $logContent.Length))
  exit 1
}