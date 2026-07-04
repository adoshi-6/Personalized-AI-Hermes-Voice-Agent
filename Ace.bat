@echo off
title ACE Protocol — Starting...
color 0A

echo.
echo  ================================================
echo    ACE — Initializing...
echo  ================================================
echo.

:: ── EDIT THIS PATH to wherever your ace folder lives ──
set ACE_DIR=C:\Users\Aryan\OneDrive\Desktop\ace

cd /d "%ACE_DIR%"
if errorlevel 1 (
    echo ERROR: Could not find the ace folder at %ACE_DIR%
    echo Edit this .bat file and update ACE_DIR to the correct path.
    pause
    exit /b 1
)

:: Activate virtual environment if present
if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

:: Start the Ace server in the background
echo Starting Ace server...
start /B python server.py > ace_log.txt 2>&1

:: Wait for the server to be ready
echo Waiting for server to come online...
:WAITLOOP
timeout /t 1 /nobreak >nul
curl -s http://localhost:5000 >nul 2>&1
if errorlevel 1 goto WAITLOOP

:: Open Ace in the default browser
echo Opening Ace in your browser...
start "" "http://localhost:5000"

echo.
echo  Ace is running. Close this window to shut Ace down.
echo  (Closing this window will stop the server.)
echo.

:: Keep the window open — closing it kills the server
:: This also shows the live server log so you can see what Ace is doing
echo  ── Live log ──────────────────────────────────────
type ace_log.txt
python server.py

pause