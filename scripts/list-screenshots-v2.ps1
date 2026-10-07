# list-screenshots-v2.ps1
Get-ChildItem 'g:\iMato\tests\test-results\auto-test\screenshots\*.png' |
  ForEach-Object {
    $line = "{0,-40} {1,8} bytes" -f $_.Name, $_.Length
    Write-Host $line
  } |
  Sort-Object
