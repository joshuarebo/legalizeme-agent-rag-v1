#!/bin/bash

# ===========================================
# LegalizeMe AI Agent - Development Cleanup
# ===========================================

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

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Function to clean Python cache
clean_python_cache() {
    print_status "Cleaning Python cache files..."
    
    # Remove __pycache__ directories
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    
    # Remove .pyc files
    find . -name "*.pyc" -delete 2>/dev/null || true
    
    # Remove .pyo files
    find . -name "*.pyo" -delete 2>/dev/null || true
    
    print_success "Python cache cleaned"
}

# Function to clean logs
clean_logs() {
    print_status "Cleaning log files..."
    
    if [ -d "logs" ]; then
        rm -rf logs/*
        print_success "Log files cleaned"
    else
        print_warning "No logs directory found"
    fi
}

# Function to clean temporary files
clean_temp_files() {
    print_status "Cleaning temporary files..."
    
    # Clean data/temp_pdfs
    if [ -d "data/temp_pdfs" ]; then
        rm -rf data/temp_pdfs/*
        print_success "Temporary PDFs cleaned"
    fi
    
    # Clean any .tmp files
    find . -name "*.tmp" -delete 2>/dev/null || true
    
    # Clean any .lock files
    find . -name "*.lock" -delete 2>/dev/null || true
    
    print_success "Temporary files cleaned"
}

# Function to clean model cache
clean_model_cache() {
    print_status "Cleaning model cache..."
    
    if [ -d "data/model_cache" ]; then
        read -p "This will remove all cached models. Are you sure? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf data/model_cache/*
            print_success "Model cache cleaned"
        else
            print_warning "Model cache cleaning skipped"
        fi
    else
        print_warning "No model cache directory found"
    fi
}

# Function to clean vector database
clean_vector_db() {
    print_status "Cleaning vector database..."
    
    if [ -d "data/vector_db" ]; then
        read -p "This will remove the vector database. Are you sure? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf data/vector_db/*
            print_success "Vector database cleaned"
        else
            print_warning "Vector database cleaning skipped"
        fi
    else
        print_warning "No vector database directory found"
    fi
}

# Function to clean virtual environment
clean_venv() {
    print_status "Cleaning virtual environment..."
    
    if [ -d "venv" ]; then
        read -p "This will remove the virtual environment. Are you sure? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf venv/
            print_success "Virtual environment removed"
            print_warning "Run ./scripts/dev-setup.sh to recreate the environment"
        else
            print_warning "Virtual environment cleaning skipped"
        fi
    else
        print_warning "No virtual environment found"
    fi
}

# Function to clean Docker artifacts
clean_docker() {
    print_status "Cleaning Docker artifacts..."
    
    if command -v docker &> /dev/null; then
        # Remove dangling images
        docker image prune -f 2>/dev/null || true
        
        # Remove unused containers
        docker container prune -f 2>/dev/null || true
        
        print_success "Docker artifacts cleaned"
    else
        print_warning "Docker not found, skipping Docker cleanup"
    fi
}

# Show help
show_help() {
    print_header "🧹 LegalizeMe AI Agent - Development Cleanup"
    echo
    echo "Usage: ./scripts/dev-clean.sh [OPTIONS]"
    echo
    echo "Options:"
    echo "  --all        Clean everything (except venv and databases)"
    echo "  --cache      Clean Python cache and temporary files"
    echo "  --logs       Clean log files"
    echo "  --models     Clean model cache (interactive)"
    echo "  --vector     Clean vector database (interactive)"
    echo "  --venv       Remove virtual environment (interactive)"
    echo "  --docker     Clean Docker artifacts"
    echo "  --help       Show this help message"
    echo
    echo "Examples:"
    echo "  ./scripts/dev-clean.sh --all"
    echo "  ./scripts/dev-clean.sh --cache --logs"
    echo "  ./scripts/dev-clean.sh --models --vector"
}

# Parse arguments
case "${1:-help}" in
    "--all")
        print_header "🧹 Complete Cleanup"
        clean_python_cache
        clean_logs
        clean_temp_files
        clean_docker
        print_success "Complete cleanup finished!"
        ;;
    "--cache")
        clean_python_cache
        clean_temp_files
        ;;
    "--logs")
        clean_logs
        ;;
    "--models")
        clean_model_cache
        ;;
    "--vector")
        clean_vector_db
        ;;
    "--venv")
        clean_venv
        ;;
    "--docker")
        clean_docker
        ;;
    "--help"|"help"|*)
        show_help
        ;;
esac