@echo off
echo Installing dependencies for Counsel Legal AI Backend...

REM Create and activate a virtual environment if needed
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate the virtual environment
call venv\Scripts\activate.bat

REM Install core dependencies
echo Installing core dependencies from requirements.txt...
pip install -r requirements.txt

REM Install specific dependencies for Phase 1
echo Installing Phase 1 dependencies...

REM Install LangGraph (graph-based workflow)
echo Installing LangGraph...
pip install langgraph==0.1.11

REM Install Haystack for RAG
echo Installing Haystack...
pip install haystack-ai==2.0.0

REM Install document processing libraries
echo Installing document processing libraries...
pip install unstructured==0.12.0 pymupdf==1.23.16

REM Install vector database
echo Installing vector database libraries...
pip install faiss-cpu==1.7.4

REM Install LLM and embedding libraries
echo Installing LLM and embedding libraries...
pip install huggingface_hub==0.20.3 transformers==4.38.1 sentence-transformers==2.3.1
pip install accelerate==0.26.1 bitsandbytes==0.41.1

REM Add additional dependencies for PDF processing
echo Installing additional PDF processing dependencies...
pip install pdf2image==1.17.0

REM Run patch imports - this will now only patch if packages are missing
echo Running patch imports...
python -m app.utils.patch_imports

echo.
echo Dependencies installed successfully!
echo.
echo Creating necessary directories...
mkdir data\vector_db 2>nul
mkdir data\temp_pdfs 2>nul
mkdir data\cache 2>nul
mkdir data\model_cache 2>nul
mkdir logs 2>nul

echo.
echo Setup complete! To start the application, run: python start_app.py
