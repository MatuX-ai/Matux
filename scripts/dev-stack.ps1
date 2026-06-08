<#
  scripts/dev-stack.ps1
  快速管理 iMato 项目的后端 (FastAPI) + 前端 (Angular dev server)

  用法:
    powershell -File scripts/dev-stack.ps1 start      # 启动两个
    powershell -File scripts/dev-stack.ps1 stop       # 停掉两个
    powershell -File scripts/dev-stack.ps1 restart    # 重启两个
    powershell -File scripts/dev-stack.ps1 status     # 查看状态
    powershell -File scripts/dev-stack.ps1 logs       # tail -f 日志 (Ctrl+C 退出)
#>

$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $Root 'backend'
$FrontendDir = $Root
$LogDir = Join-Path $Root 'logs'
$BackendLog = Join-Path $LogDir 'backend.log'
$BackendErr = Join-Path $LogDir 'backend.log.err'
$FrontendLog = Join-Path $LogDir 'frontend.log'
$FrontendErr = Join-Path $LogDir 'frontend.log.err'
$PythonExe = Join-Path $BackendDir 'venv\Scripts\python.exe'
$NgCmd = Join-Path $Root 'node_modules\.bin\ng.cmd'

if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }

# 允许跨域的源（前端 4200）
$AllowedOrigins = 'http://localhost:3000,http://localhost:4200,http://127.0.0.1:3000,http://127.0.0.1:4200,http://127.0.0.1:8080'

function Get-PortOwner($port) {
  Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty OwningProcess
}

function Stop-ByPort($port, [string]$label) {
  $pid_ = Get-PortOwner $port
  if ($pid_) {
    try { Stop-Process -Id $pid_ -Force -ErrorAction SilentlyContinue; Write-Host "stopped $label (pid=$pid_, port=$port)" -ForegroundColor Yellow }
    catch { Write-Host "failed to stop $label" -ForegroundColor Red }
  } else {
    Write-Host "$label not running on port $port"
  }
}

function Wait-PortFree($port, $timeoutSec = 8) {
  $deadline = (Get-Date).AddSeconds($timeoutSec)
  while ((Get-Date) -lt $deadline) {
    if (-not (Get-PortOwner $port)) { return $true }
    Start-Sleep -Milliseconds 300
  }
  return $false
}

function Start-Backend {
  Write-Host 'starting backend (uvicorn 127.0.0.1:8000) ...' -ForegroundColor Cyan
  $env:ALLOWED_ORIGINS = $AllowedOrigins
  $env:PYTHONUNBUFFERED = '1'
  $p = Start-Process -FilePath $PythonExe -ArgumentList @(
    '-m','uvicorn','main:app','--host','127.0.0.1','--port','8000','--log-level','info'
  ) -WorkingDirectory $BackendDir -RedirectStandardOutput $BackendLog -RedirectStandardError $BackendErr -WindowStyle Hidden -PassThru
  Write-Host "backend pid=$($p.Id) log=$BackendLog" -ForegroundColor Green
  return $p.Id
}

function Start-Frontend {
  Write-Host 'starting frontend (ng serve 127.0.0.1:4200) ...' -ForegroundColor Cyan
  $p = Start-Process -FilePath $NgCmd -ArgumentList @(
    'serve','--host','127.0.0.1','--port','4200','--no-open'
  ) -WorkingDirectory $FrontendDir -RedirectStandardOutput $FrontendLog -RedirectStandardError $FrontendErr -WindowStyle Hidden -PassThru
  Write-Host "frontend pid=$($p.Id) log=$FrontendLog" -ForegroundColor Green
  return $p.Id
}

function Show-Status {
  $bp = Get-PortOwner 8000
  $fp = Get-PortOwner 4200
  Write-Host ''
  Write-Host '=== dev stack status ===' -ForegroundColor Cyan
  Write-Host ("backend  8000 : {0}" -f $(if ($bp) { "running (pid=$bp, log=logs\backend.log)" } else { 'STOPPED' }))
  Write-Host ("frontend 4200 : {0}" -f $(if ($fp) { "running (pid=$fp, log=logs\frontend.log)" } else { 'STOPPED' }))
  Write-Host ''
}

function Wait-Health {
  Write-Host 'waiting for backend /health ...' -ForegroundColor DarkCyan
  $deadline = (Get-Date).AddSeconds(60)
  while ((Get-Date) -lt $deadline) {
    try {
      $r = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/health' -TimeoutSec 3
      if ($r.status) { Write-Host "backend health: $($r.status)" -ForegroundColor Green; return }
    } catch { }
    Start-Sleep -Seconds 1
  }
  Write-Host 'backend did not become healthy in 60s' -ForegroundColor Red
}

switch ($args[0]) {
  'start' {
    if (-not (Get-PortOwner 8000)) { Start-Backend | Out-Null; Wait-Health } else { Write-Host 'backend already running' }
    if (-not (Get-PortOwner 4200)) { Start-Frontend | Out-Null } else { Write-Host 'frontend already running' }
    Show-Status
  }
  'stop' {
    Stop-ByPort 4200 'frontend'
    Stop-ByPort 8000 'backend'
    Wait-PortFree 4200 | Out-Null
    Wait-PortFree 8000 | Out-Null
    Show-Status
  }
  'restart' {
    & $PSCommandPath stop
    Start-Sleep -Seconds 1
    & $PSCommandPath start
  }
  'start-backend' {
    if (-not (Get-PortOwner 8000)) { Start-Backend | Out-Null; Wait-Health } else { Write-Host 'backend already running' }
    Show-Status
  }
  'stop-backend' {
    Stop-ByPort 8000 'backend'
    Wait-PortFree 8000 | Out-Null
    Show-Status
  }
  'restart-backend' {
    & $PSCommandPath stop-backend
    Start-Sleep -Seconds 1
    & $PSCommandPath start-backend
  }
  'start-frontend' {
    if (-not (Get-PortOwner 4200)) { Start-Frontend | Out-Null } else { Write-Host 'frontend already running' }
    Show-Status
  }
  'stop-frontend' {
    Stop-ByPort 4200 'frontend'
    Wait-PortFree 4200 | Out-Null
    Show-Status
  }
  'restart-frontend' {
    & $PSCommandPath stop-frontend
    Start-Sleep -Seconds 1
    & $PSCommandPath start-frontend
  }
  'status' { Show-Status }
  'logs' {
    Write-Host 'tailing logs (Ctrl+C to stop):' -ForegroundColor Cyan
    Get-Content $BackendLog, $FrontendLog -Tail 30 -Wait -Encoding UTF8
  }
  'logs-backend' {
    Get-Content $BackendLog -Tail 30 -Wait -Encoding UTF8
  }
  'logs-frontend' {
    Get-Content $FrontendLog -Tail 30 -Wait -Encoding UTF8
  }
  default {
    Write-Host 'usage: dev-stack.ps1 {start|stop|restart|status|logs}' -ForegroundColor Yellow
    Write-Host '       {start|stop|restart}-{backend|frontend}' -ForegroundColor Yellow
    Write-Host '       logs-{backend|frontend}' -ForegroundColor Yellow
  }
}
