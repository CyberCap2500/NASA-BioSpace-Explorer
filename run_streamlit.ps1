# NASA Space Biology Knowledge Engine - Standalone Streamlit App
# This script runs the complete search engine in a single Streamlit app

Write-Host "NASA Space Biology Knowledge Engine - Standalone" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
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

# Check essential data files
Write-Host "Checking data files..." -ForegroundColor Yellow
$dataFiles = @(
    "backend/data/metadata.sqlite",
    "backend/vector_store/faiss_index",
    "backend/vector_store/faiss_index.ids"
)

$missingFiles = @()
foreach ($file in $dataFiles) {
    if (Test-Path $file) {
        $size = (Get-Item $file).Length
        Write-Host "Found: $file ($size bytes)" -ForegroundColor Green
    } else {
        $missingFiles += $file
        Write-Host "Missing: $file" -ForegroundColor Red
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host "ERROR: Missing essential data files!" -ForegroundColor Red
    Write-Host "Please run data ingestion first:" -ForegroundColor Yellow
    Write-Host "  cd backend && python ingest_and_embed.py" -ForegroundColor Gray
    Read-Host "Press Enter to exit"
    exit 1
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
} else {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    .\.venv\Scripts\Activate.ps1
}

Write-Host ""
Write-Host "Starting NASA BioSpace Explorer..." -ForegroundColor Cyan
Write-Host "App will open at: http://localhost:8501" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the app" -ForegroundColor Yellow
Write-Host ""

# Start Streamlit app
streamlit run streamlit_standalone.py --server.port 8501
