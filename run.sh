#!/bin/bash
# Counsel startup script for Linux/Mac

echo "Starting Counsel - Legal AI Assistant..."
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python is not installed. Please install Python 3.11+"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Check if requirements are installed
if [ ! -d "venv/lib/python3.11/site-packages/fastapi" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Create data directories
mkdir -p data/temp_pdfs
mkdir -p data/vector_db
mkdir -p logs

# Start the application
echo
echo "Starting the API server..."
python -m app.main "$@"

# Deactivate virtual environment
deactivate
