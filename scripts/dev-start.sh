#!/bin/bash

# ===========================================
# LegalizeMe AI Agent - Development Server
# ===========================================

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_error "Virtual environment not found. Please run ./scripts/dev-setup.sh first."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error ".env file not found. Please run ./scripts/dev-setup.sh first."
    exit 1
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Check if port is already in use
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_error "Port 8000 is already in use. Please stop the other service first."
    exit 1
fi

# Start the server
print_status "Starting development server..."
print_success "🚀 LegalizeMe AI Agent is starting..."
echo
echo "Access the API at: http://localhost:8000"
echo "View API docs at: http://localhost:8000/docs"
echo "Press Ctrl+C to stop the server"
echo

# Start uvicorn with reload
python -m uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000 --log-level info