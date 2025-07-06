#!/bin/bash

# ===========================================
# LegalizeMe AI Agent - Test Runner
# ===========================================

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
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

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_error "Virtual environment not found. Please run ./scripts/dev-setup.sh first."
    exit 1
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Set test environment variables
export TEST_MODE=true
export DEBUG_MODE=false
export ENABLE_CRAWLER=false

print_status "Running LegalizeMe AI Agent test suite..."

# Run different test suites based on arguments
case "${1:-all}" in
    "unit")
        print_status "Running unit tests..."
        if [ -d "tests" ]; then
            python -m pytest tests/ -v --tb=short
        else
            print_warning "No tests directory found. Skipping unit tests."
        fi
        ;;
    "integration")
        print_status "Running integration tests..."
        if [ -f "scripts/test_multi_llm.py" ]; then
            python scripts/test_multi_llm.py
        else
            print_warning "Integration test script not found."
        fi
        ;;
    "api")
        print_status "Running API tests..."
        if [ -f "scripts/smoke_test_claude.py" ]; then
            python scripts/smoke_test_claude.py
        else
            print_warning "API test script not found."
        fi
        ;;
    "all"|*)
        print_status "Running all tests..."
        
        # Unit tests
        if [ -d "tests" ]; then
            print_status "1. Running unit tests..."
            python -m pytest tests/ -v --tb=short || print_warning "Some unit tests failed"
        fi
        
        # Integration tests
        if [ -f "scripts/test_multi_llm.py" ]; then
            print_status "2. Running integration tests..."
            python scripts/test_multi_llm.py || print_warning "Some integration tests failed"
        fi
        
        # API tests
        if [ -f "scripts/smoke_test_claude.py" ]; then
            print_status "3. Running API smoke tests..."
            python scripts/smoke_test_claude.py || print_warning "Some API tests failed"
        fi
        
        # Health check
        print_status "4. Running health check..."
        if python -c "from app.api.main import app; print('✓ Application imports successfully')" 2>/dev/null; then
            print_success "Health check passed"
        else
            print_error "Health check failed"
        fi
        ;;
esac

print_success "Test suite completed!"
echo
echo "Usage: ./scripts/dev-test.sh [unit|integration|api|all]"
echo "  unit        - Run unit tests only"
echo "  integration - Run integration tests only"
echo "  api         - Run API tests only"
echo "  all         - Run all tests (default)"