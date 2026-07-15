@echo off
echo ===================================================
echo   Watch Out - Safety Monitoring System
echo ===================================================
echo.
echo [1/2] Opening browser: http://127.0.0.1:8000
start "" "http://127.0.0.1:8000"
echo.
echo [2/2] Starting backend (FastAPI + frontend)...
echo       Press Ctrl+C to stop.
echo.
.venv\Scripts\python.exe src/api/server.py
pause
