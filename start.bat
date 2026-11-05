@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Starting Financial System for LAN access...
echo On this server: http://localhost:8000
echo On employee PCs: http://SERVER-IP:8000
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000
pause
