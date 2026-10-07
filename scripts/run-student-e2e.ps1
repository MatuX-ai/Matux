#Requires -Version 5.1
<#
.SYNOPSIS
  iMato student-end E2E test one-click entry

.DESCRIPTION
  Pipeline: clear ports -> create accounts -> start backend -> health check ->
            start Electron (CDP) -> run test engine -> collect reports

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File g:\iMato\scripts\run-student-e2e.ps1

.NOTES
  Exit codes:
    0 = all passed
    1 = some page failed
    2 = backend not ready
    3 = Electron CDP not ready
#>

$ErrorActionPreference = 'Continue'
Set-Location g:\iMato

$gPython     = 'g:\Python312\python.exe'
$gElectron   = 'g:\iMato\electron\node_modules\electron\dist\electron.exe'
$TestEngine  = 'g:\iMato\tests\electron\auto-test\run.js'
$ReportDir   = 'g:\iMato\test-results\auto-test'
$LogDir      = $ReportDir
$BackendCwd  = 'g:\iMato\backend'
$ElectronCwd = 'g:\iMato\electron'

if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

function Cleanup-Ports {
    foreach ($p in @(8000, 9222, 4200)) {
        $conns = Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue
        foreach ($c in $conns) {
            try { Stop-Process -Id $c.OwningProcess -Force -ErrorAction Stop } catch {}
        }
    }
    $singleton = "$env:APPDATA\imato\Singleton*"
    $files = Get-ChildItem -Path $singleton -ErrorAction SilentlyContinue
    foreach ($f in $files) {
        try { Remove-Item -Path $f.FullName -Force -ErrorAction Stop } catch {}
    }
}

function Wait-HttpOk {
    param(
        [string]$Url,
        [int]$TimeoutSec = 60,
        [string]$Label = 'service'
    )
    for ($i = 0; $i -lt $TimeoutSec; $i++) {
        try {
            $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
            if ($r.StatusCode -eq 200) {
                return $true
            }
        } catch {}
        Start-Sleep -Seconds 1
    }
    Write-Host "  [FAIL] $Label not ready in ${TimeoutSec}s" -ForegroundColor Red
    return $false
}

# ===== Step 1: Clear ports and stale files =====
Write-Host ''
Write-Host '[1/7] Clear ports 8000/9222/4200 and SingletonLock...' -ForegroundColor Cyan
Cleanup-Ports
Start-Sleep -Seconds 1

# ===== Step 2: Create test accounts =====
Write-Host ''
Write-Host '[2/7] Create test accounts (test_student)...' -ForegroundColor Cyan
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
$accountsLog = Join-Path $LogDir 'create-accounts.log'
& $gPython "$BackendCwd\create_test_accounts.py" 2>&1 | Out-File -FilePath $accountsLog -Encoding utf8

# ===== Step 3: Start backend =====
Write-Host ''
Write-Host '[3/7] Start backend (main_ai_edu.py)...' -ForegroundColor Cyan
$env:PORT = '8000'
$backendStdout = Join-Path $LogDir 'backend-stdout.log'
$backendStderr = Join-Path $LogDir 'backend-stderr.log'
$backendProc = Start-Process -FilePath $gPython `
    -ArgumentList 'main_ai_edu.py' `
    -WorkingDirectory $BackendCwd `
    -RedirectStandardOutput $backendStdout `
    -RedirectStandardError $backendStderr `
    -PassThru -WindowStyle Hidden

# ===== Step 4: Wait for backend health =====
Write-Host ''
Write-Host '[4/7] Wait for backend /health...' -ForegroundColor Cyan
$ready = Wait-HttpOk -Url 'http://localhost:8000/health' -TimeoutSec 180 -Label 'backend'
if (-not $ready) {
    try { Stop-Process -Id $backendProc.Id -Force } catch {}
    exit 2
}
Write-Host '  [OK] backend health check passed' -ForegroundColor Green

# ===== Step 5: Start Electron (CDP) =====
Write-Host ''
Write-Host '[5/7] Start Electron (CDP 9222)...' -ForegroundColor Cyan
$env:NODE_ENV = 'production'
$electronStdout = Join-Path $LogDir 'electron-stdout.log'
$electronStderr = Join-Path $LogDir 'electron-stderr.log'
$electronProc = Start-Process -FilePath $gElectron `
    -ArgumentList @('.', '--remote-debugging-port=9222') `
    -WorkingDirectory $ElectronCwd `
    -RedirectStandardOutput $electronStdout `
    -RedirectStandardError $electronStderr `
    -PassThru -WindowStyle Hidden

$cdpReady = Wait-HttpOk -Url 'http://localhost:9222/json' -TimeoutSec 60 -Label 'Electron CDP'
if (-not $cdpReady) {
    try { Stop-Process -Id $electronProc.Id -Force } catch {}
    try { Stop-Process -Id $backendProc.Id -Force } catch {}
    exit 3
}
Write-Host '  [OK] Electron CDP ready' -ForegroundColor Green

# ===== Step 6: Run test engine =====
Write-Host ''
Write-Host '[6/7] Run test engine (student, 19 pages, app:// protocol)...' -ForegroundColor Cyan
$env:FRONTEND_URL       = 'app://./index.html'
$env:BACKEND_HEALTH_URL = 'http://localhost:8000/health'
$env:API_BASE_URL       = 'http://localhost:8000'
$env:CDP_PORT           = '9222'

$engineLog = Join-Path $LogDir 'engine-stdout.log'
& 'g:\nodejs\node.exe' $TestEngine --account student --cdp-port 9222 --no-kill 2>&1 | Out-File -FilePath $engineLog -Encoding utf8
$exitCode = $LASTEXITCODE

# ===== Step 7: Cleanup =====
Write-Host ''
Write-Host '[7/7] Cleanup...' -ForegroundColor Cyan
try { Stop-Process -Id $electronProc.Id -Force -ErrorAction SilentlyContinue } catch {}
try { Stop-Process -Id $backendProc.Id -Force -ErrorAction SilentlyContinue } catch {}
Cleanup-Ports

$reportFiles = Get-ChildItem -Path "$ReportDir\test-report-*.html" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
Write-Host ''
if ($reportFiles) {
    Write-Host "[REPORT] $($reportFiles.FullName)" -ForegroundColor Yellow
} else {
    Write-Host '[WARN] no HTML report found' -ForegroundColor Yellow
}

exit $exitCode