@echo off
REM Host the BeeBuzz Monitor on your local network (Windows).
REM
REM Usage:   serve.bat [port]
REM Default port: 8000
REM
REM Requires Python 3 (https://www.python.org/downloads/  - tick "Add to PATH").
REM Binds to 0.0.0.0 so other devices on the same Wi-Fi/LAN can open it at:
REM     http://<this-PC-IP>:<port>
REM
REM Note: Web Serial (Connect Arduino) only works on localhost or https.
REM       Over plain http on the LAN, use Demo mode on other devices.

setlocal
set PORT=%1
if "%PORT%"=="" set PORT=8000

set DIR=%~dp0

echo.
echo Serving %DIR% on port %PORT%
echo.
echo This PC's addresses (open one of these from another device):
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do echo    http://%%a:%PORT%/index.html
echo.
echo Press Ctrl+C to stop.
echo.

python -m http.server %PORT% --bind 0.0.0.0 --directory "%DIR%"
if errorlevel 1 (
  echo.
  echo Python not found. Trying the 'py' launcher...
  py -m http.server %PORT% --bind 0.0.0.0 --directory "%DIR%"
)

endlocal
