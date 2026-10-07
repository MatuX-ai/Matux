# Manual run script - assumes backend (8000) and Electron CDP (9222) are already running
$ErrorActionPreference = 'Continue'

$env:FRONTEND_URL       = 'app://./index.html'
$env:BACKEND_HEALTH_URL = 'http://localhost:8000/health'
$env:API_BASE_URL       = 'http://localhost:8000'
$env:CDP_PORT           = '9222'
$env:NODE_ENV           = 'production'

Set-Location g:\iMato

$engineLog = 'g:\iMato\test-results\auto-test\manual-engine.log'
& 'g:\nodejs\node.exe' 'g:\iMato\tests\electron\auto-test\run.js' --account student --cdp-port 9222 --no-kill 2>&1 | Out-File -FilePath $engineLog -Encoding utf8
exit $LASTEXITCODE