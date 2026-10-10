# Script to start both IncidentFlow Backend and Frontend

$ProjectRoot = Get-Location

Write-Host Starting FastAPI Backend on port 8000... -ForegroundColor Green
$BackendJob = Start-Job -ScriptBlock {
    param($Root)
    Set-Location (Join-Path $Root backend)
    & (Join-Path $Root venv\Scripts\python.exe) -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
} -ArgumentList $ProjectRoot

Write-Host Starting IncidentFlow React Frontend on port 5173... -ForegroundColor Green
$FrontendJob = Start-Job -ScriptBlock {
    param($Root)
    Set-Location (Join-Path $Root frontend-react)
    npm run dev
} -ArgumentList $ProjectRoot

Write-Host ---------------------------------------- -ForegroundColor Cyan
Write-Host IncidentFlow is running! -ForegroundColor Cyan
Write-Host Frontend UI: http://localhost:5173 -ForegroundColor Cyan
Write-Host Backend API: http://127.0.0.1:8000 -ForegroundColor Cyan
Write-Host API Docs: http://127.0.0.1:8000/docs -ForegroundColor Cyan
Write-Host ---------------------------------------- -ForegroundColor Cyan
Write-Host Press Ctrl+C to stop both servers. -ForegroundColor Yellow

try {
    Receive-Job -Job $BackendJob, $FrontendJob -Wait
}
finally {
    Write-Host Stopping servers... -ForegroundColor Red
    Stop-Job -Job $BackendJob, $FrontendJob
    Remove-Job -Job $BackendJob, $FrontendJob
}
