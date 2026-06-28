@echo off
REM Host the BeeBuzz Monitor on your local network (Windows).
REM
REM Usage:   serve.bat [port]
REM Default port: 8000
REM
REM Requires Python 3 (https://www.python.org/downloads/  - tick "Add to PATH").
REM Binds to 0.0.0.0 so other devices on the same Wi-Fi/LAN can open it at:
REM     http://<this-PC-IP>:<port>/
REM
REM Note: Web Serial (Connect Arduino) only works on localhost or https.
REM       Over plain http on the LAN, use Demo mode on other devices.

setlocal enabledelayedexpansion
set PORT=%1
if "%PORT%"=="" set PORT=8000

REM Serve from the folder this script lives in
cd /d "%~dp0"

if not exist "index.html" (
  echo ERROR: index.html not found in "%CD%".
  echo Put serve.bat in the same folder as index.html.
  pause
  exit /b 1
)

REM Find a working Python
set PY=
where python >nul 2>&1 && set PY=python
if "!PY!"=="" ( where py >nul 2>&1 && set PY=py )
if "!PY!"=="" (
  echo ERROR: Python not found. Install it from https://www.python.org/downloads/
  echo Make sure to tick "Add Python to PATH" during install.
  pause
  exit /b 1
)

echo.
echo Serving "%CD%" on port %PORT%
echo.
echo Open from another device on the same network:
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
  set IP=%%a
  set IP=!IP: =!
  echo    http://!IP!:%PORT%/
)
echo On this PC use:  http://localhost:%PORT%/
echo.
echo Press Ctrl+C to stop.
echo.

!PY! -m http.server %PORT% --bind 0.0.0.0

echo.
echo Server stopped.
pause
endlocal
