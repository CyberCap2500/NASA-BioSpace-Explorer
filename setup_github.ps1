# GitHub Setup Script for NASA Space Biology Knowledge Engine
# This script helps you set up GitHub repository and deploy to Streamlit Cloud

Write-Host "GitHub + Streamlit Cloud Deployment Setup" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check if git is installed
try {
    $gitVersion = git --version 2>&1
    Write-Host "Git found: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "Git not found! Please install Git from https://git-scm.com" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check essential data files
Write-Host "Checking essential data files..." -ForegroundColor Yellow
$dataFiles = @(
    "backend/data/metadata.sqlite",
    "backend/vector_store/faiss_index",
    "backend/vector_store/faiss_index.ids",
    "backend/database/SB_publication_PMC.csv"
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

# Initialize git repository
if (-not (Test-Path ".git")) {
    Write-Host "Initializing Git repository..." -ForegroundColor Yellow
    git init
    git add .
    git commit -m "Initial commit: NASA Space Biology Knowledge Engine"
    Write-Host "Git repository initialized!" -ForegroundColor Green
} else {
    Write-Host "Git repository already exists" -ForegroundColor Green
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Create a new repository on GitHub:" -ForegroundColor White
Write-Host "   https://github.com/new" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Repository name: nasa-space-biology-engine" -ForegroundColor White
Write-Host "   Make it PUBLIC (required for free Streamlit Cloud)" -ForegroundColor Yellow
Write-Host ""
Write-Host "3. After creating the repo, run these commands:" -ForegroundColor White
Write-Host "   git remote add origin https://github.com/YOUR_USERNAME/nasa-space-biology-engine.git" -ForegroundColor Gray
Write-Host "   git branch -M main" -ForegroundColor Gray
Write-Host "   git push -u origin main" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Deploy to Streamlit Cloud:" -ForegroundColor White
Write-Host "   Go to: https://share.streamlit.io" -ForegroundColor Gray
Write-Host "   Connect your GitHub repository" -ForegroundColor Gray
Write-Host "   Main file: streamlit_app_cloud.py" -ForegroundColor Gray
Write-Host ""
Write-Host "5. Your app will be live at:" -ForegroundColor White
Write-Host "   https://YOUR_USERNAME-nasa-space-biology-engine.streamlit.app" -ForegroundColor Gray
Write-Host ""

$continue = Read-Host "Press Enter when you've created the GitHub repository, or 'q' to quit"
if ($continue -eq 'q') {
    exit 0
}

# Get repository URL from user
Write-Host ""
$repoUrl = Read-Host "Enter your GitHub repository URL (e.g., https://github.com/username/nasa-space-biology-engine.git)"

if ($repoUrl) {
    Write-Host "Adding remote origin..." -ForegroundColor Yellow
    git remote add origin $repoUrl
    git branch -M main
    
    Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
    git push -u origin main
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Successfully pushed to GitHub!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Now go to https://share.streamlit.io to deploy your app!" -ForegroundColor Cyan
    } else {
        Write-Host "Error pushing to GitHub. Please check your repository URL." -ForegroundColor Red
    }
} else {
    Write-Host "No repository URL provided. Please run the git commands manually." -ForegroundColor Yellow
}

Write-Host ""
Read-Host "Press Enter to exit"
