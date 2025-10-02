# Start Frontend UI
Write-Host "Starting NASA Space Biology Knowledge Engine - Frontend" -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Green

# Change to frontend directory
Set-Location frontend

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

# Start the Streamlit app
Write-Host "Starting Streamlit app on http://localhost:8501" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the app" -ForegroundColor Gray
streamlit run streamlit_app.py --server.port 8501
