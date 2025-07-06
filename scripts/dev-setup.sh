#!/bin/bash

# ===========================================
# LegalizeMe AI Agent - Development Setup
# ===========================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Check if Python 3.11+ is available
check_python() {
    print_status "Checking Python version..."
    
    if command -v python3.11 &> /dev/null; then
        PYTHON_CMD="python3.11"
    elif command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_error "Python is not installed. Please install Python 3.11+ first."
        exit 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version | cut -d' ' -f2)
    print_success "Found Python $PYTHON_VERSION"
    
    # Check if version is 3.11+
    if [[ $(echo "$PYTHON_VERSION" | cut -d'.' -f1) -lt 3 ]] || [[ $(echo "$PYTHON_VERSION" | cut -d'.' -f1) -eq 3 && $(echo "$PYTHON_VERSION" | cut -d'.' -f2) -lt 11 ]]; then
        print_warning "Python 3.11+ is recommended. Current version: $PYTHON_VERSION"
    fi
}

# Create virtual environment
create_venv() {
    print_status "Creating virtual environment..."
    
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists. Removing old one..."
        rm -rf venv
    fi
    
    $PYTHON_CMD -m venv venv
    print_success "Virtual environment created"
}

# Activate virtual environment
activate_venv() {
    print_status "Activating virtual environment..."
    source venv/bin/activate
    print_success "Virtual environment activated"
}

# Install dependencies
install_dependencies() {
    print_status "Installing dependencies..."
    
    # Upgrade pip first
    pip install --upgrade pip
    
    # Install requirements
    pip install -r requirements.txt
    
    print_success "Dependencies installed"
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p data/vector_db
    mkdir -p data/model_cache
    mkdir -p data/temp_pdfs
    mkdir -p data/llm_config
    mkdir -p logs
    mkdir -p tests/data
    
    print_success "Directories created"
}

# Setup environment file
setup_environment() {
    print_status "Setting up environment configuration..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_success "Environment file created from template"
            print_warning "Please edit .env file with your API keys and configuration"
        else
            print_warning "No .env.example found. Creating basic .env file..."
            cat > .env << EOF
# Basic configuration
DEBUG_MODE=true
ENVIRONMENT=development
LOG_LEVEL=INFO
PORT=8000
PRIMARY_LLM_TYPE=flan-t5
ENABLE_CRAWLER=false
EOF
            print_success "Basic .env file created"
        fi
    else
        print_warning ".env file already exists. Skipping..."
    fi
}

# Run basic health check
health_check() {
    print_status "Running health check..."
    
    # Check if we can import the main app
    if $PYTHON_CMD -c "from app.api.main import app; print('✓ App imports successfully')" 2>/dev/null; then
        print_success "Application imports working"
    else
        print_error "Application import failed. Check the logs above."
        return 1
    fi
}

# Main setup function
main() {
    print_header "🏛️  LegalizeMe AI Agent - Development Setup"
    
    echo "This script will set up your development environment for LegalizeMe AI Agent."
    echo "Press Enter to continue, or Ctrl+C to cancel..."
    read
    
    # Check if we're in the right directory
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found. Please run this script from the project root."
        exit 1
    fi
    
    # Run setup steps
    check_python
    create_venv
    activate_venv
    install_dependencies
    create_directories
    setup_environment
    health_check
    
    print_header "🎉 Setup Complete!"
    echo
    print_success "Your development environment is ready!"
    echo
    echo "Next steps:"
    echo "1. Edit .env file with your API keys (optional for basic testing)"
    echo "2. Activate virtual environment: source venv/bin/activate"
    echo "3. Start the development server: python -m uvicorn app.api.main:app --reload"
    echo "4. Access the API at: http://localhost:8000"
    echo "5. View API docs at: http://localhost:8000/docs"
    echo
    echo "Quick start commands:"
    echo "  Start server: ./scripts/dev-start.sh"
    echo "  Run tests: ./scripts/dev-test.sh"
    echo "  Clean up: ./scripts/dev-clean.sh"
}

# Run main function
main "$@"