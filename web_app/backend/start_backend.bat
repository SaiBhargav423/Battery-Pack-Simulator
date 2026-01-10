@echo off
REM Windows startup script for BMS Simulator Backend
REM This script starts the Flask backend server locally

echo ========================================
echo BMS Simulator - Local Backend Server
echo ========================================
echo.

REM Change to backend directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Check if virtual environment exists
if exist "..\..\venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call "..\..\venv\Scripts\activate.bat"
)

REM Check if dependencies are installed
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo WARNING: Flask not found. Installing dependencies...
    pip install -r requirements.txt
)

REM Check if frontend is built
if not exist "..\frontend\build\index.html" (
    echo WARNING: Frontend not built. Building now...
    cd ..\frontend
    call npm install
    call npm run build
    cd ..\backend
)

echo.
echo Starting Flask backend server...
echo Backend will be available at: http://localhost:5000
echo Frontend will be available at: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start Flask application
python app.py

pause
