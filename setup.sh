#!/usr/bin/env bash
# Quick setup script for Builder Discovery Pipeline (Linux/Mac)
set -e

echo "============================================"
echo " Builder Discovery Pipeline - Setup"
echo "============================================"
echo ""

# Check prerequisites
check_cmd() {
    if ! command -v "$1" &> /dev/null; then
        echo "ERROR: $1 is not installed. $2"
        exit 1
    fi
}

check_cmd python3 "Install from https://python.org"
check_cmd node    "Install from https://nodejs.org"
check_cmd npm     "Install from https://nodejs.org"

# Check Python version
PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "[OK] Python $PY_VERSION"

# Check Node version
NODE_VERSION=$(node --version)
echo "[OK] Node $NODE_VERSION"

# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo ""
    echo "Installing uv (Python package manager)..."
    pip install uv
fi
echo "[OK] uv installed"

# Set up environment file
if [ ! -f backend/.env ]; then
    echo ""
    echo "Creating backend/.env from template..."
    cp .env.example backend/.env
    echo ""
    echo "!!! IMPORTANT: Edit backend/.env and add your API keys !!!"
    echo "    - GITHUB_TOKEN: https://github.com/settings/tokens (public_repo scope)"
    echo "    - GEMINI_API_KEY: https://aistudio.google.com/apikey"
    echo ""
    read -p "Press Enter after you've added your API keys to backend/.env..."
fi

# Install backend dependencies
echo ""
echo "Installing backend dependencies..."
cd backend
uv sync
cd ..

# Install frontend dependencies
echo ""
echo "Installing frontend dependencies..."
cd frontend
npm install
cd ..

echo ""
echo "============================================"
echo " Setup complete!"
echo "============================================"
echo ""
echo " To start the app, open 3 terminals:"
echo ""
echo " Terminal 1 (Backend):"
echo "   cd backend && uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
echo ""
echo " Terminal 2 (Frontend):"
echo "   cd frontend && npm run dev"
echo ""
echo " Terminal 3 (Pipeline):"
echo "   cd backend && uv run python scripts/run_discovery.py full"
echo ""
echo " Dashboard: http://localhost:3000"
echo " API Docs:  http://127.0.0.1:8000/docs"
echo ""
