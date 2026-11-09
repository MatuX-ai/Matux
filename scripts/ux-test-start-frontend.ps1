$ErrorActionPreference = 'Stop'
$Root = 'I:\iMato'
$LogDir = Join-Path $Root 'logs'
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
$FrontendLog = Join-Path $LogDir 'frontend.log'
$FrontendErr = Join-Path $LogDir 'frontend.log.err'
$NgCmd = Join-Path $Root 'node_modules\.bin\ng.cmd'

Write-Host 'starting ng serve on 127.0.0.1:4200 ...' -ForegroundColor Cyan
$p = Start-Process -FilePath $NgCmd -ArgumentList @(
  'serve','--host','127.0.0.1','--port','4200','--no-open','--poll=2000'
) -WorkingDirectory $Root -RedirectStandardOutput $FrontendLog -RedirectStandardError $FrontendErr -WindowStyle Hidden -PassThru

Write-Host ("ng pid={0} log={1}" -f $p.Id, $FrontendLog) -ForegroundColor Green
Start-Sleep -Seconds 3
Get-Process -Id $p.Id -ErrorAction SilentlyContinue | Select-Object Id, ProcessName | Format-Table -AutoSize
