@echo off
setlocal enabledelayedexpansion

:: Set working directory to script location
cd /d "%~dp0"

:: Activate Python virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Please run: python -m venv venv
    echo Then run: venv\Scripts\pip install -r requirements.txt
    exit /b 1
)

:: Change to viz directory
cd viz

:: Run Streamlit dashboard with public access and authentication
echo Starting public dashboard at %date% %time%
set STREAMLIT_SERVER_PORT=8501
set STREAMLIT_SERVER_ADDRESS=0.0.0.0
streamlit run app.py
if !errorlevel! neq 0 (
    echo Dashboard failed to start with error code !errorlevel!
    exit /b !errorlevel!
)

:: Deactivate virtual environment
deactivate 