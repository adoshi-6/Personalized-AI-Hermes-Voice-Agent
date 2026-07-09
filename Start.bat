@echo off
title Voice Assistant — Starting...
color 0A

echo.
echo  ================================================
echo    Voice Assistant — Initializing...
echo  ================================================
echo.

:: ── EDIT THIS PATH to wherever your project folder lives ──
:: By default, uses the folder this .bat file is in.
set ACE_DIR=%~dp0

cd /d "%ACE_DIR%"
if errorlevel 1 (
    echo ERROR: Could not find the project folder at %ACE_DIR%
    echo Edit this .bat file and update ACE_DIR to the correct path.
    pause
    exit /b 1
)

:: Activate virtual environment if present
if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

:: Start the server in the background
echo Starting server...
start /B python server.py > assistant_log.txt 2>&1

:: Wait for the server to be ready
echo Waiting for server to come online...
:WAITLOOP
timeout /t 1 /nobreak >nul
curl -s http://localhost:5000 >nul 2>&1
if errorlevel 1 goto WAITLOOP

:: Open the dashboard in the default browser
echo Opening dashboard in your browser...
start "" "http://localhost:5000"

echo.
echo  Assistant is running. Close this window to shut it down.
echo  (Closing this window will stop the server.)
echo.

:: Keep the window open — closing it kills the server
:: This also shows the live server log so you can see what's happening
echo  ── Live log ──────────────────────────────────────
type assistant_log.txt
python server.py

pause
