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

:: Run ETL process
echo Starting ETL process at %date% %time%
python ETL_main.py
if !errorlevel! neq 0 (
    echo ETL process failed with error code !errorlevel!
    exit /b !errorlevel!
)

echo ETL process completed successfully at %date% %time%

:: Deactivate virtual environment
deactivate 

echo Pulling latest updates from Github
git pull