@echo off
echo ===================================================
echo   Watch Out - Safety Monitoring System Launcher
echo ===================================================
echo.
echo [1/2] Tarayici aciliyor: http://127.0.0.1:8000
start "" "http://127.0.0.1:8000"
echo.
echo [2/2] Flask sunucusu (Backend + Frontend) baslatiliyor...
echo.
.venv\Scripts\python.exe src/api/server.py
pause
