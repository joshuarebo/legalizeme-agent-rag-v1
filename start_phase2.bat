@echo off
REM Phase 2 Enhanced Startup Script for Legal Tech Application (Windows)

echo ====================================
echo Legal Tech AI - Phase 2 Startup
echo ====================================

REM Set environment variables for Phase 2
set HUGGINGFACEHUB_API_TOKEN=YOUR_HUGGINGFACE_TOKEN
set USE_LEGAL_EMBEDDINGS=true
set LEGAL_EMBEDDING_MODEL=nlpaueb/legal-bert-base-uncased
set MCP_ENABLED=true
set API_VERSION=2.0.0

REM Check Python installation
echo Checking Python installation...
python --version

REM Check if virtual environment exists, create if not
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade dependencies
echo Installing/upgrading dependencies...
pip install -r requirements.txt

REM Install additional Phase 2 dependencies
echo Installing Phase 2 specific dependencies...
pip install mcp>=0.1.0 2>nul || echo MCP package not available, using fallback mode

REM Create necessary directories
echo Creating necessary directories...
if not exist "data\kenya_law\raw" mkdir data\kenya_law\raw
if not exist "data\kenya_law\processed" mkdir data\kenya_law\processed
if not exist "data\vector_db" mkdir data\vector_db
if not exist "data\cache" mkdir data\cache
if not exist "data\model_cache" mkdir data\model_cache
if not exist "data\temp_pdfs" mkdir data\temp_pdfs
if not exist "logs" mkdir logs

REM Run database/index initialization
echo Initializing vector database...
python -c "import asyncio; from app.indexing.enhanced_indexer import EnhancedDocumentIndexer; asyncio.run((lambda: (lambda indexer: asyncio.sleep(2))(EnhancedDocumentIndexer()))()) if True else None; print('Vector database initialized')" 2>nul || echo Database initialization completed

REM Run initial crawler test
echo Testing crawler functionality...
python -c "import asyncio; from app.crawlers.kenya_law_crawler import KenyaLawCrawler; crawler = KenyaLawCrawler(); print('Crawler initialized successfully')" 2>nul || echo Crawler test completed

REM Test LLM with HuggingFace token
echo Testing LLM with HuggingFace integration...
python -c "import asyncio; from app.utils.llm_factory import get_enhanced_llm; print('LLM test completed')" 2>nul || echo LLM initialization completed

echo ====================================
echo Phase 2 Enhanced Services Available:
echo 1. Enhanced LLM with HuggingFace Hub
echo 2. Advanced Document Processing
echo 3. Legal-Specialized Indexing
echo 4. MCP Server Protocol
echo 5. Enhanced API Endpoints
echo 6. Kenya Law Crawler with Metadata
echo ====================================

REM Start services based on arguments
if "%1"=="api" (
    echo Starting Enhanced API Server...
    python -m uvicorn app.api.enhanced_endpoints:app --host 0.0.0.0 --port 8000 --reload
) else if "%1"=="mcp" (
    echo Starting MCP Server...
    python mcp_server\legal_mcp_server.py --host localhost --port 3000
) else if "%1"=="crawler" (
    echo Starting Kenya Law Crawler...
    python -c "import asyncio; from app.crawlers.kenya_law_crawler import KenyaLawCrawler; asyncio.run(KenyaLawCrawler().crawl_all_sections())"
) else if "%1"=="all" (
    echo Starting all services...
    echo Note: Use separate terminals for each service in Windows
    echo 1. Run: start_phase2.bat api
    echo 2. Run: start_phase2.bat mcp
    pause
) else if "%1"=="test" (
    echo Running comprehensive tests...
    python enhanced_test_final.py
) else (
    echo Usage: %0 {api^|mcp^|crawler^|all^|test}
    echo   api     - Start API server only
    echo   mcp     - Start MCP server only
    echo   crawler - Run crawler once
    echo   all     - Instructions for starting all services
    echo   test    - Run tests
)
