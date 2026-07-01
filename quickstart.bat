@echo off
REM Product Sentiment Analyzer - Quick Start Script for Windows
REM Run this script to setup and start the application

cls
echo.
echo ============================================================
echo.   Product Sentiment Analyzer - Quick Start (Windows)
echo.
echo ============================================================
echo.

REM Check Python installation
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.8+
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo   Found: %PYTHON_VERSION%
echo.

REM Create virtual environment
echo Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo   Virtual environment created
) else (
    echo   Virtual environment already exists
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo   Activated
echo.

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt -q
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo   Dependencies installed
echo.

REM Check .env file
echo Checking configuration...
if not exist ".env" (
    echo   WARNING: .env file not found!
    echo.
    echo   Please create .env file with MongoDB URI:
    echo.
    echo   MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true^&w=majority
    echo   MONGO_DB_NAME=product_sentiment
    echo.
    set /p CONFIGURED="Have you configured .env? (y/n): "
    if /i not "%CONFIGURED%"=="y" (
        exit /b 1
    )
) else (
    echo   .env file found
)
echo.

REM Create required directories
echo Setting up directories...
if not exist "exports" mkdir exports
if not exist "data" mkdir data
if not exist "templates" mkdir templates
if not exist "static\css" mkdir static\css
if not exist "static\js" mkdir static\js
echo   Directories ready
echo.

REM Display startup info
echo.
echo ============================================================
echo   Ready to start!
echo ============================================================
echo.
echo   Command: python app.py
echo   Then open: http://localhost:5000
echo.
echo   Features:
echo   * Scrape reviews from Amazon and Flipkart
echo   * AI-powered sentiment analysis
echo   * Interactive analytics dashboard
echo   * Export data as CSV or JSON
echo.
echo ============================================================
echo.

REM Ask to start
set /p START_NOW="Start the application now? (y/n): "
if /i "%START_NOW%"=="y" (
    echo.
    echo Starting application...
    echo.
    python app.py
) else (
    echo.
    echo To start manually, run: python app.py
    echo.
)

pause
