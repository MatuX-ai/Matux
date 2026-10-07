# List-screenshots.ps1
Get-ChildItem "g:\iMato\tests\test-results\auto-test\screenshots\*.png" |
  ForEach-Object { "{0}  {1} bytes" -f $_.Name, $_.Length } |
  Sort-Object |
  Write-Host
