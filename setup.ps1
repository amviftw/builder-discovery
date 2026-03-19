# Quick setup script for Builder Discovery Pipeline (Windows PowerShell)
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Builder Discovery Pipeline - Setup" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
function Check-Command($cmd, $installUrl) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        Write-Host "ERROR: $cmd is not installed. Install from $installUrl" -ForegroundColor Red
        exit 1
    }
}

Check-Command "python" "https://python.org"
Check-Command "node" "https://nodejs.org"
Check-Command "npm" "https://nodejs.org"

$pyVersion = python --version 2>&1
Write-Host "[OK] $pyVersion" -ForegroundColor Green

$nodeVersion = node --version 2>&1
Write-Host "[OK] Node $nodeVersion" -ForegroundColor Green

# Install uv if not present
if (-not (Get-Command "uv" -ErrorAction SilentlyContinue)) {
    Write-Host ""
    Write-Host "Installing uv (Python package manager)..." -ForegroundColor Yellow
    pip install uv
}
Write-Host "[OK] uv installed" -ForegroundColor Green

# Set up environment file
if (-not (Test-Path "backend\.env")) {
    Write-Host ""
    Write-Host "Creating backend\.env from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" "backend\.env"
    Write-Host ""
    Write-Host "!!! IMPORTANT: Edit backend\.env and add your API keys !!!" -ForegroundColor Red
    Write-Host "    - GITHUB_TOKEN: https://github.com/settings/tokens (public_repo scope)" -ForegroundColor Yellow
    Write-Host "    - GEMINI_API_KEY: https://aistudio.google.com/apikey" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter after you've added your API keys to backend\.env"
}

# Install backend dependencies
Write-Host ""
Write-Host "Installing backend dependencies..." -ForegroundColor Yellow
Push-Location backend
uv sync
Pop-Location

# Install frontend dependencies
Write-Host ""
Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
Push-Location frontend
npm install
Pop-Location

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Setup complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host " To start the app, open 3 terminals:" -ForegroundColor White
Write-Host ""
Write-Host " Terminal 1 (Backend):" -ForegroundColor Yellow
Write-Host "   cd backend; uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload" -ForegroundColor White
Write-Host ""
Write-Host " Terminal 2 (Frontend):" -ForegroundColor Yellow
Write-Host "   cd frontend; npm run dev" -ForegroundColor White
Write-Host ""
Write-Host " Terminal 3 (Pipeline):" -ForegroundColor Yellow
Write-Host "   cd backend; uv run python scripts/run_discovery.py full" -ForegroundColor White
Write-Host ""
Write-Host " Dashboard: http://localhost:3000" -ForegroundColor Green
Write-Host " API Docs:  http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host ""
