@echo off
title CHRONOS Protocol — Starting...
color 0A

echo.
echo  ================================================
echo    CHRONOS — Initializing...
echo  ================================================
echo.

:: ── EDIT THIS PATH to wherever your chronos folder lives ──
set CHRONOS_DIR=C:\Users\Aryan\OneDrive\Desktop\CHRONOS

cd /d "%CHRONOS_DIR%"
if errorlevel 1 (
    echo ERROR: Could not find the chronos folder at %CHRONOS_DIR%
    echo Edit this .bat file and update CHRONOS_DIR to the correct path.
    pause
    exit /b 1
)

:: Activate virtual environment if present
if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

:: Make sure "python" actually resolves before we try to use it.
:: (This replaces a hardcoded path that doesn't exist on most machines
:: and was silently failing the server launch.)
where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: "python" was not found on PATH.
    echo Activate the correct virtual environment or fix your PATH, then re-run this file.
    pause
    exit /b 1
)

:: Start the Chronos server in the background, tied to this console window
echo Starting Chronos server...
start /B python server.py > chronos_log.txt 2>&1

:: Wait for the server to be ready — with a real timeout so this can't hang forever
echo Waiting for server to come online...
set WAIT_COUNT=0
:WAITLOOP
timeout /t 1 /nobreak >nul
set /a WAIT_COUNT+=1
curl -s -o nul http://localhost:5000
if not errorlevel 1 goto SERVER_UP
if %WAIT_COUNT% GEQ 30 (
    echo.
    echo ERROR: Server did not come online after 30 seconds.
    echo Here is the log so far:
    echo -- chronos_log.txt ---------------------------------
    type chronos_log.txt
    echo -----------------------------------------------------
    pause
    exit /b 1
)
goto WAITLOOP

:SERVER_UP
echo Server is online.

:: Open Chronos in Google Chrome specifically -- with a fallback if Chrome
:: isn't installed at one of the two standard locations.
echo Opening Chronos in your browser...
set CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe
if not exist "%CHROME_PATH%" set CHROME_PATH=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe

if exist "%CHROME_PATH%" (
    start "" "%CHROME_PATH%" "http://localhost:5000"
) else (
    echo Chrome was not found at the usual install path -- opening your default browser instead.
    start "" "http://localhost:5000"
)

echo.
echo  Chronos is running. Close this window to shut Chronos down.
echo  (Closing this window will stop the server.)
echo.
echo  -- Live log ------------------------------------------
powershell -NoProfile -Command "Get-Content -Path 'chronos_log.txt' -Wait"

pause