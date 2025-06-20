@echo off
echo Running Enhanced Test for Counsel Legal AI Backend...
echo.

REM Activate the virtual environment
call venv\Scripts\activate.bat

REM Run the enhanced test script
python enhanced_test.py

REM Pause at the end to see results
pause
