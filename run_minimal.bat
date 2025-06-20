@echo off
:: Run script for Counsel Legal AI with minimal dependencies
:: This script runs the application with only essential dependencies

echo Setting up Counsel Legal AI (minimal mode)...

:: Create a virtual environment if it doesn't exist
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

:: Activate the virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

:: Install or update minimal dependencies
echo Installing minimal dependencies...
pip install fastapi uvicorn python-dotenv
pip install langchain openai chromadb

:: Create stubs directory structure
echo Creating stub directories...
mkdir "app\utils\stubs" 2>nul
mkdir "app\utils\stubs\haystack" 2>nul
mkdir "app\utils\stubs\haystack\document_stores" 2>nul
mkdir "app\utils\stubs\unstructured" 2>nul
mkdir "app\utils\stubs\unstructured\partition" 2>nul
mkdir "app\utils\stubs\smol_agent" 2>nul

:: Create stubs for each problematic package
echo Creating stubs for problematic packages...

:: Langgraph stub
echo # Stub implementation for langgraph> app\utils\stubs\langgraph.py
echo class StateGraph:>> app\utils\stubs\langgraph.py
echo     def __init__(self, *args, **kwargs):>> app\utils\stubs\langgraph.py
echo         pass>> app\utils\stubs\langgraph.py
echo     def add_node(self, *args, **kwargs):>> app\utils\stubs\langgraph.py
echo         return self>> app\utils\stubs\langgraph.py
echo     def add_edge(self, *args, **kwargs):>> app\utils\stubs\langgraph.py
echo         return self>> app\utils\stubs\langgraph.py
echo     def set_entry_point(self, *args, **kwargs):>> app\utils\stubs\langgraph.py
echo         return self>> app\utils\stubs\langgraph.py
echo     def compile(self, *args, **kwargs):>> app\utils\stubs\langgraph.py
echo         return self>> app\utils\stubs\langgraph.py
echo class ToolNode:>> app\utils\stubs\langgraph.py
echo     def __init__(self, *args, **kwargs):>> app\utils\stubs\langgraph.py
echo         pass>> app\utils\stubs\langgraph.py
echo END = "END">> app\utils\stubs\langgraph.py
echo class prebuilt:>> app\utils\stubs\langgraph.py
echo     class ToolNode:>> app\utils\stubs\langgraph.py
echo         def __init__(self, *args, **kwargs):>> app\utils\stubs\langgraph.py
echo             pass>> app\utils\stubs\langgraph.py

:: Create init files
echo # Init file> app\utils\stubs\__init__.py
echo # Init file> app\utils\stubs\haystack\__init__.py
echo # Init file> app\utils\stubs\haystack\document_stores\__init__.py
echo # Init file> app\utils\stubs\unstructured\__init__.py
echo # Init file> app\utils\stubs\unstructured\partition\__init__.py
echo # Init file> app\utils\stubs\smol_agent\__init__.py

:: Create necessary directories
echo Creating necessary directories...
mkdir "data\vector_db" 2>nul
mkdir "data\model_cache" 2>nul
mkdir "data\temp_pdfs" 2>nul
mkdir "data\llm_config" 2>nul
mkdir "logs" 2>nul

:: Create a basic startup script that uses stubs
echo Creating minimal startup script...
echo import sys> start_app.py
echo import os>> start_app.py
echo.>> start_app.py
echo # Add the app directory to the Python path>> start_app.py
echo app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))>> start_app.py
echo if app_dir not in sys.path:>> start_app.py
echo     sys.path.insert(0, app_dir)>> start_app.py
echo.>> start_app.py
echo # Set up stubs for missing modules>> start_app.py
echo print("Setting up stubs for missing modules...")>> start_app.py
echo.>> start_app.py
echo # Define stub creator function>> start_app.py
echo def create_stub_module(name):>> start_app.py
echo     class StubModule:>> start_app.py
echo         def __init__(self, name):>> start_app.py
echo             self.__name__ = name>> start_app.py
echo             self.cuda = self  # For torch compatibility>> start_app.py
echo             self.device = "cpu"  # For torch compatibility>> start_app.py
echo         def is_available(self):  # For torch compatibility>> start_app.py
echo             return False>> start_app.py
echo         def __getattr__(self, attr):>> start_app.py
echo             def stub_callable(*args, **kwargs):>> start_app.py
echo                 return None>> start_app.py
echo             return stub_callable>> start_app.py
echo     stub = StubModule(name)>> start_app.py
echo     sys.modules[name] = stub>> start_app.py
echo     return stub>> start_app.py
echo.>> start_app.py
echo # Create stubs for common problematic modules>> start_app.py
echo for module_name in ['langgraph', 'haystack', 'unstructured', 'fitz', 'smol_agent', 'torch']:>> start_app.py
echo     try:>> start_app.py
echo         __import__(module_name)>> start_app.py
echo         print(f"Successfully imported {module_name}")>> start_app.py
echo     except ImportError:>> start_app.py
echo         print(f"Creating stub for {module_name}")>> start_app.py
echo         create_stub_module(module_name)>> start_app.py
echo.>> start_app.py
echo # Run the application>> start_app.py
echo try:>> start_app.py
echo     print("Starting Counsel Legal AI application...")>> start_app.py
echo     import uvicorn>> start_app.py
echo     uvicorn.run('app.api.main:app', host='0.0.0.0', port=8000)>> start_app.py
echo except Exception as e:>> start_app.py
echo     print(f"Error starting the application: {e}")>> start_app.py
echo     import traceback>> start_app.py
echo     traceback.print_exc()>> start_app.py
echo     input("Press Enter to exit...")>> start_app.py

:: Run the application
echo Starting Counsel Legal AI application (minimal mode)...
python start_app.py

:: Keep the window open
echo.
echo Press any key to exit...
pause > nul
pip install faiss-cpu
pip install transformers
pip install beautifulsoup4 httpx aiohttp

:: Create stubs for missing modules
echo Creating stubs for missing modules...
mkdir "app\utils\stubs" 2>nul

:: Create langgraph stub
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
echo END = "END">> app\utils\stubs\langgraph.py

:: Create necessary directories
echo Creating necessary directories...
mkdir "data\vector_db" 2>nul
mkdir "data\model_cache" 2>nul
mkdir "data\temp_pdfs" 2>nul
mkdir "data\llm_config" 2>nul
mkdir "logs" 2>nul

:: Apply patches for modules
echo Patching imports in modules...
python -m app.utils.patch_imports

:: Run the application
echo Starting Counsel Legal AI application in development mode...
python -m app.main

:: Keep the window open
echo.
echo Press any key to exit...
pause > nul
