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

:: Run Streamlit dashboard
echo Starting dashboard at %date% %time%
streamlit run app.py --server.port 8501 --server.address localhost
if !errorlevel! neq 0 (
    echo Dashboard failed to start with error code !errorlevel!
    exit /b !errorlevel!
)

:: Deactivate virtual environment (though we shouldn't reach this point as Streamlit runs continuously)
deactivate 