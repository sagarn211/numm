$ErrorActionPreference = "Stop"

Set-Location "$PSScriptRoot\..\backend"

if (Test-Path "..\.venv\Scripts\Activate.ps1") {
    & "..\.venv\Scripts\Activate.ps1"
} elseif (Test-Path ".\venv\Scripts\Activate.ps1") {
    & ".\venv\Scripts\Activate.ps1"
}

alembic upgrade head
uvicorn app.main:app --reload --port 8000
