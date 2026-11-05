@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
title Financial System - PostgreSQL Central Server

set PY=
where py >nul 2>nul && set PY=py -3
if not defined PY (where python >nul 2>nul && set PY=python)
if not defined PY (
  echo [ERROR] Python 3.10+ is not installed. Install it from python.org and tick Add to PATH.
  pause & exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  %PY% -m venv .venv || (echo [ERROR] Could not create virtual environment.& pause & exit /b 1)
)
set VPY=.venv\Scripts\python.exe
if not exist ".venv\.deps_ok" (
  echo Installing required packages...
  "%VPY%" -m pip install --upgrade pip
  "%VPY%" -m pip install -r requirements.txt || (echo [ERROR] Package installation failed.& pause & exit /b 1)
  echo ok> ".venv\.deps_ok"
)
if not exist ".env" (
  echo First run: configure PostgreSQL connection.
  "%VPY%" setup_central_server.py
  if errorlevel 1 (pause & exit /b 1)
) else (
  echo Using existing .env settings; no database is reset or recreated.
)
"%VPY%" check_postgres_connection.py
if errorlevel 1 (echo [ERROR] PostgreSQL connection failed. No app startup attempted.& pause & exit /b 1)
echo.
echo Starting application on all network interfaces at port 8000.
echo Other computers should browse to http://SERVER-IP:8000
"%VPY%" -m uvicorn app.main:app --host 0.0.0.0 --port 8000
pause
