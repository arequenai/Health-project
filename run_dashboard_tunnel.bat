@echo off
setlocal enabledelayedexpansion

:: Set working directory to script location
cd /d "%~dp0"

:: Start Streamlit in one terminal
start cmd /k "venv\Scripts\activate && cd viz && streamlit run app.py"

:: Wait for Streamlit to start
timeout /t 5

:: Start Cloudflare tunnel in another terminal
start cmd /k "cloudflared.exe tunnel --url http://localhost:8501"

echo Dashboard started! When Cloudflare gives you a URL, you can access your dashboard there.
echo Press any key to stop both the dashboard and the tunnel...
pause

:: Kill both processes
taskkill /F /IM streamlit.exe
taskkill /F /IM cloudflared.exe 