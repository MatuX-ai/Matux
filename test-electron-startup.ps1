# 【端口说明】与 start-electron.bat 保持一致：使用 launcher.js 默认端口 8000
# 备用端口：8001, 8002, 8003, 8080, 3001（见 electron/config/constants.js）
# 后端启动失败时 launcher.js 会自动尝试备用端口
$env:BACKEND_PORT = "8000"
# 【修复 #8】不设置 NODE_ENV=development，走 app:// 加载本地 dist，避免与 ng serve 冲突
# 需要热重载开发时手动设置 $env:NODE_ENV = "development"
$env:NODE_ENV = "production"
$logFile = "g:\iMato\electron-clean-startup.log"
$stdoutFile = "g:\iMato\electron-clean-stdout.log"
$stderrFile = "g:\iMato\electron-clean-stderr.log"

Remove-Item $logFile, $stdoutFile, $stderrFile -ErrorAction SilentlyContinue

$startTime = Get-Date
$timestamp = Get-Date -Format 'HH:mm:ss.fff'
"Start Time: $timestamp" | Out-File -FilePath $logFile -Encoding utf8

Set-Location "g:\iMato\electron"
$proc = Start-Process -FilePath "g:\iMato\electron\node_modules\electron\dist\electron.exe" `
                       -ArgumentList "." `
                       -PassThru `
                       -RedirectStandardOutput $stdoutFile `
                       -RedirectStandardError $stderrFile
"PID: $($proc.Id)" | Out-File -FilePath $logFile -Append -Encoding utf8

$timeoutSec = 60
$checkInterval = 5
$elapsed = 0
$crashed = $false
$windowShown = $false

while ($elapsed -lt $timeoutSec) {
    Start-Sleep -Seconds $checkInterval
    $elapsed += $checkInterval
    $proc.Refresh()
    $currentTime = Get-Date -Format 'HH:mm:ss.fff'
    $status = ""
    if ($proc.HasExited) {
        $status = "EXITED ExitCode=$($proc.ExitCode)"
        $crashed = $true
    } else {
        $title = $proc.MainWindowTitle
        if ($title -and $title.Length -gt 0) {
            $windowShown = $true
            $status = "ALIVE Window='$title'"
        } else {
            $status = "ALIVE Window=(none)"
        }
    }
    "[+$($elapsed)s $currentTime] $status" | Out-File -FilePath $logFile -Append -Encoding utf8
    if ($crashed) { break }
}

$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds
"End Time: $(Get-Date -Format 'HH:mm:ss.fff')" | Out-File -FilePath $logFile -Append -Encoding utf8
"Total Duration: ${duration}s" | Out-File -FilePath $logFile -Append -Encoding utf8
if ($proc.HasExited) {
    "Timeout Status: YES (process exited)" | Out-File -FilePath $logFile -Append -Encoding utf8
} else {
    "Timeout Status: NO (process still running)" | Out-File -FilePath $logFile -Append -Encoding utf8
}
if ($windowShown) {
    "Window Status: SHOWN" | Out-File -FilePath $logFile -Append -Encoding utf8
} else {
    "Window Status: NOT SHOWN" | Out-File -FilePath $logFile -Append -Encoding utf8
}

if (-not $proc.HasExited) {
    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
}

Get-Content $logFile