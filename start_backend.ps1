# Start Backend API Server
Write-Host "Starting NASA Space Biology Knowledge Engine - Backend" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green

# Change to backend directory
Set-Location backend

# Activate virtual environment
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    . .\.venv\Scripts\Activate.ps1
} else {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    . .\.venv\Scripts\Activate.ps1
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
}

# Set environment variables
$env:PYTHONPATH = "."

# Start the API server
Write-Host "Starting FastAPI server on http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Gray
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
