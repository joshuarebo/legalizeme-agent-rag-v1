@echo off
rem Counsel startup script for Windows

echo Starting Counsel - Legal AI Assistant...
echo.

rem Check if Python is installed
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH. Please install Python 3.11+.
    exit /b 1
)

rem Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

rem Activate virtual environment
call venv\Scripts\activate.bat

rem Check if requirements are installed
if not exist venv\Lib\site-packages\fastapi (
    echo Installing dependencies...
    pip install -r requirements.txt
)

rem Create data directories
if not exist data\temp_pdfs mkdir data\temp_pdfs
if not exist data\vector_db mkdir data\vector_db
if not exist logs mkdir logs

rem Start the application
echo.
echo Starting the API server...
python -m app.main %*

rem Deactivate virtual environment
call venv\Scripts\deactivate.bat
