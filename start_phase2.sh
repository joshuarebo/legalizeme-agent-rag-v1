#!/bin/bash
# Phase 2 Enhanced Startup Script for Legal Tech Application

echo "===================================="
echo "Legal Tech AI - Phase 2 Startup"
echo "===================================="

# Set environment variables for Phase 2
export HUGGINGFACEHUB_API_TOKEN="YOUR_HUGGINGFACE_TOKEN"
export USE_LEGAL_EMBEDDINGS="true"
export LEGAL_EMBEDDING_MODEL="nlpaueb/legal-bert-base-uncased"
export MCP_ENABLED="true"
export API_VERSION="2.0.0"

# Check Python installation
echo "Checking Python installation..."
python --version

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "Installing/upgrading dependencies..."
pip install -r requirements.txt

# Install additional Phase 2 dependencies
echo "Installing Phase 2 specific dependencies..."
pip install mcp>=0.1.0 2>/dev/null || echo "MCP package not available, using fallback mode"

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p data/kenya_law/raw
mkdir -p data/kenya_law/processed
mkdir -p data/vector_db
mkdir -p data/cache
mkdir -p data/model_cache
mkdir -p data/temp_pdfs
mkdir -p logs

# Run database/index initialization
echo "Initializing vector database..."
python -c "
import asyncio
from app.indexing.enhanced_indexer import EnhancedDocumentIndexer
async def init():
    indexer = EnhancedDocumentIndexer()
    await asyncio.sleep(2)  # Allow initialization
    print('Vector database initialized')
try:
    asyncio.run(init())
except Exception as e:
    print(f'Database initialization: {e}')
"

# Run initial crawler test
echo "Testing crawler functionality..."
python -c "
import asyncio
from app.crawlers.kenya_law_crawler import KenyaLawCrawler
async def test():
    crawler = KenyaLawCrawler()
    print('Crawler initialized successfully')
try:
    asyncio.run(test())
except Exception as e:
    print(f'Crawler test: {e}')
"

# Test LLM with HuggingFace token
echo "Testing LLM with HuggingFace integration..."
python -c "
import asyncio
from app.utils.llm_factory import get_enhanced_llm
async def test():
    llm = get_enhanced_llm('huggingface', 'legal_reasoning')
    try:
        response = await llm.invoke('Test legal query')
        print('LLM test successful')
    except Exception as e:
        print(f'LLM test: {e}')
try:
    asyncio.run(test())
except Exception as e:
    print(f'LLM initialization: {e}')
"

echo "===================================="
echo "Phase 2 Enhanced Services Available:"
echo "1. Enhanced LLM with HuggingFace Hub"
echo "2. Advanced Document Processing"
echo "3. Legal-Specialized Indexing"
echo "4. MCP Server Protocol"
echo "5. Enhanced API Endpoints"
echo "6. Kenya Law Crawler with Metadata"
echo "===================================="

# Start services based on arguments
case "${1:-api}" in
    "api")
        echo "Starting Enhanced API Server..."
        python -m uvicorn app.api.enhanced_endpoints:app --host 0.0.0.0 --port 8000 --reload
        ;;
    "mcp")
        echo "Starting MCP Server..."
        python mcp_server/legal_mcp_server.py --host localhost --port 3000
        ;;
    "crawler")
        echo "Starting Kenya Law Crawler..."
        python -c "
import asyncio
from app.crawlers.kenya_law_crawler import KenyaLawCrawler
async def main():
    crawler = KenyaLawCrawler()
    await crawler.crawl_all_sections()
asyncio.run(main())
        "
        ;;
    "all")
        echo "Starting all services..."
        # Start API server in background
        python -m uvicorn app.api.enhanced_endpoints:app --host 0.0.0.0 --port 8000 &
        
        # Start MCP server in background
        python mcp_server/legal_mcp_server.py --host localhost --port 3000 &
        
        # Keep script running
        wait
        ;;
    "test")
        echo "Running comprehensive tests..."
        python enhanced_test_final.py
        ;;
    *)
        echo "Usage: $0 {api|mcp|crawler|all|test}"
        echo "  api     - Start API server only"
        echo "  mcp     - Start MCP server only"
        echo "  crawler - Run crawler once"
        echo "  all     - Start all services"
        echo "  test    - Run tests"
        ;;
esac
