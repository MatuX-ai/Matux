$ErrorActionPreference = 'Stop'
$Root = 'I:\iMato'
$LogDir = Join-Path $Root 'logs'
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
$NgTestLog = Join-Path $LogDir 'ng-test.log'
$NgTestErr = Join-Path $LogDir 'ng-test.log.err'
$NgCmd = Join-Path $Root 'node_modules\.bin\ng.cmd'

# Karma needs Chrome binary env var
$env:CHROME_BIN = 'C:\Program Files\Google\Chrome\Application\chrome.exe'

# 7 P0 gamification spec files (must be exactly the same pattern as karma --include)
$SpecFiles = @(
  'src/app/core/services/level-title.service.spec.ts',
  'src/app/core/services/level-event.service.spec.ts',
  'src/app/core/services/daily-checkin.service.spec.ts',
  'src/app/core/services/ai-fab-state.service.spec.ts',
  'src/app/core/services/feedback-fly.service.spec.ts',
  'src/app/shared/components/sparkle-burst/sparkle-burst.component.spec.ts',
  'src/app/shared/components/level-up-modal/level-up-modal.component.spec.ts'
)

# Build --include args
$IncludeArgs = ($SpecFiles | ForEach-Object { '--include=' + $_ }) -join ' '

Write-Host "starting ng test (7 P0 specs) ..." -ForegroundColor Cyan
$p = Start-Process -FilePath $NgCmd -ArgumentList @(
  'test','--watch=false','--browsers=ChromeHeadlessNoSandbox','--no-progress',
  '--code-coverage=false','--reporters=progress'
) -WorkingDirectory $Root -RedirectStandardOutput $NgTestLog -RedirectStandardError $NgTestErr -WindowStyle Hidden -PassThru

Write-Host ("ng-test pid={0} log={1}" -f $p.Id, $NgTestLog) -ForegroundColor Green
Start-Sleep -Seconds 2
Get-Process -Id $p.Id -ErrorAction SilentlyContinue | Select-Object Id, ProcessName | Format-Table -AutoSize
