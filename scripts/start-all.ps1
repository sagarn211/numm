$root = Resolve-Path "$PSScriptRoot\.."

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root'; .\scripts\start-backend.ps1"
Start-Sleep -Seconds 2

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root'; .\scripts\start-ai.ps1"
Start-Sleep -Seconds 2

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root'; .\scripts\start-mock-sap.ps1"
Start-Sleep -Seconds 2

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root'; .\scripts\start-frontend.ps1"

Write-Host ""
Write-Host "NUMM services started:"
Write-Host "Frontend : http://localhost:5173"
Write-Host "Backend  : http://localhost:8000/docs"
Write-Host "AI       : http://localhost:8001/docs"
Write-Host "Mock SAP : http://localhost:8002/docs"
