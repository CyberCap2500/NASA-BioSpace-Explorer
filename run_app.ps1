# NASA Space Biology Knowledge Engine - One-Click Launcher
# This script sets up everything and runs the app automatically

Write-Host "NASA Space Biology Knowledge Engine" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python not found! Please install Python 3.8+ from https://python.org" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Create virtual environments if they don't exist
Write-Host "Setting up environments..." -ForegroundColor Yellow

# Backend setup
if (-not (Test-Path "backend\.venv")) {
    Write-Host "Creating backend environment..." -ForegroundColor Gray
    Set-Location backend
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    Set-Location ..
}

# Frontend setup
if (-not (Test-Path "frontend\.venv")) {
    Write-Host "Creating frontend environment..." -ForegroundColor Gray
    Set-Location frontend
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    Set-Location ..
}

Write-Host "Environments ready!" -ForegroundColor Green
Write-Host ""

# Start backend in background
Write-Host "Starting backend API..." -ForegroundColor Yellow
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD\backend
    .\.venv\Scripts\Activate.ps1
    $env:PYTHONPATH = "."
    python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
}

# Wait a moment for backend to start
Start-Sleep -Seconds 3

# Start frontend
Write-Host "Starting web interface..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Your app will open at: http://localhost:8501" -ForegroundColor Cyan
Write-Host "API running at: http://127.0.0.1:8000" -ForegroundColor Gray
Write-Host ""
Write-Host "Press Ctrl+C to stop both services" -ForegroundColor Yellow
Write-Host ""

Set-Location frontend
.\.venv\Scripts\Activate.ps1
streamlit run streamlit_app.py --server.port 8501

# Cleanup when frontend stops
Write-Host ""
Write-Host "Stopping backend..." -ForegroundColor Yellow
Stop-Job $backendJob
Remove-Job $backendJob
Write-Host "All services stopped!" -ForegroundColor Green
