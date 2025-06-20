@echo off
:: Setup and run script for Counsel Legal AI
:: This script creates a virtual environment, installs dependencies, and runs the application

echo Setting up Counsel Legal AI...

:: Try to run the PowerShell script first (preferred method)
where powershell >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo Using PowerShell for enhanced setup...
    powershell -ExecutionPolicy Bypass -File "%~dp0run_app.ps1"
    if %ERRORLEVEL% equ 0 (
        :: PowerShell script ran successfully
        echo.
        echo Application has stopped.
        pause
        exit /b 0
    )
    echo PowerShell script failed, falling back to batch script...
)

:: Create a virtual environment if it doesn't exist
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

:: Activate the virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

:: Install or update dependencies
echo Installing dependencies...
:: First, install core packages
pip install fastapi uvicorn python-dotenv
pip install langchain
pip install faiss-cpu
pip install transformers

:: Try to install langgraph
pip install langgraph

:: Create stubs directory for potential fallbacks
mkdir "app\utils\stubs" 2>nul
mkdir "app\utils\stubs\haystack" 2>nul
mkdir "app\utils\stubs\haystack\document_stores" 2>nul
mkdir "app\utils\stubs\unstructured" 2>nul
mkdir "app\utils\stubs\unstructured\partition" 2>nul
mkdir "app\utils\stubs\smol_agent" 2>nul

:: Check if langgraph installation succeeded
python -c "import langgraph" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Warning: Could not install langgraph. Using stub implementation.
    :: Create a stub for langgraph if it fails to install
    echo # Stub implementation for langgraph> app\utils\stubs\langgraph.py
    echo class StateGraph:>> app\utils\stubs\langgraph.py
    echo     def __init__(self, *args, **kwargs):>> app\utils\stubs\langgraph.py
    echo         pass>> app\utils\stubs\langgraph.py
    echo.>> app\utils\stubs\langgraph.py
    echo     def add_node(self, *args, **kwargs):>> app\utils\stubs\langgraph.py
    echo         return self>> app\utils\stubs\langgraph.py
    echo.>> app\utils\stubs\langgraph.py
    echo     def add_edge(self, *args, **kwargs):>> app\utils\stubs\langgraph.py
    echo         return self>> app\utils\stubs\langgraph.py
    echo.>> app\utils\stubs\langgraph.py
    echo     def set_entry_point(self, *args, **kwargs):>> app\utils\stubs\langgraph.py
    echo         return self>> app\utils\stubs\langgraph.py
    echo.>> app\utils\stubs\langgraph.py
    echo     def compile(self, *args, **kwargs):>> app\utils\stubs\langgraph.py
    echo         return self>> app\utils\stubs\langgraph.py
    echo.>> app\utils\stubs\langgraph.py
    echo class ToolNode:>> app\utils\stubs\langgraph.py
    echo     def __init__(self, *args, **kwargs):>> app\utils\stubs\langgraph.py
    echo         pass>> app\utils\stubs\langgraph.py
    echo.>> app\utils\stubs\langgraph.py
    echo END = "END">> app\utils\stubs\langgraph.py
    echo.>> app\utils\stubs\langgraph.py
    echo # Add prebuilt module with ToolNode>> app\utils\stubs\langgraph.py
    echo class prebuilt:>> app\utils\stubs\langgraph.py
    echo     class ToolNode:>> app\utils\stubs\langgraph.py
    echo         def __init__(self, *args, **kwargs):>> app\utils\stubs\langgraph.py
    echo             pass>> app\utils\stubs\langgraph.py
)

:: Create filtered requirements file without problematic packages
echo Creating filtered requirements file...
type nul > requirements-filtered.txt
for /F "tokens=*" %%A in (requirements.txt) do (
    echo %%A | findstr /V "smol-agent weaviate-client flash-attn langgraph llama-index" >> requirements-filtered.txt
)

:: Install filtered requirements
pip install -r requirements-filtered.txt --no-deps

:: Create necessary directories
echo Creating necessary directories...
mkdir "data\vector_db" 2>nul
mkdir "data\model_cache" 2>nul
mkdir "data\temp_pdfs" 2>nul
mkdir "data\llm_config" 2>nul
mkdir "logs" 2>nul

:: Apply patches for missing modules if needed
echo Applying patches for missing modules...
python -m app.utils.patch_imports

:: Create a custom startup script
echo Preparing startup script...
echo import sys> start_app.py
echo import os>> start_app.py
echo.>> start_app.py
echo # Add the app directory to the Python path>> start_app.py
echo app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))>> start_app.py
echo if app_dir not in sys.path:>> start_app.py
echo     sys.path.insert(0, app_dir)>> start_app.py
echo.>> start_app.py
echo # Import stubs first>> start_app.py
echo try:>> start_app.py
echo     from app.utils.stubs import langgraph>> start_app.py
echo     from app.utils.stubs import haystack>> start_app.py
echo     import app.utils.stubs.unstructured>> start_app.py
echo     import app.utils.stubs.fitz>> start_app.py
echo except ImportError as e:>> start_app.py
echo     print(f"Error importing stubs: {e}")>> start_app.py
echo.>> start_app.py
echo # Patch imports in key files>> start_app.py
echo import os>> start_app.py
echo import uvicorn>> start_app.py
echo.>> start_app.py
echo # Run the application with error handling>> start_app.py
echo try:>> start_app.py
echo     uvicorn.run('app.api.main:app', host='0.0.0.0', port=8000)>> start_app.py
echo except Exception as e:>> start_app.py
echo     print(f"Error starting the application: {e}")>> start_app.py
echo     import traceback>> start_app.py
echo     traceback.print_exc()>> start_app.py

:: Run the application
echo Starting Counsel Legal AI application...
python start_app.py

:: Keep the window open
echo.
echo Press any key to exit...
pause > nul
