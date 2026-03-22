@echo off
echo ========================================
echo   Malaysia Stock Dashboard - Windows
echo ========================================
echo.
echo Detecting your IP address...

REM Try to get Windows IP
for /f "delims= tokens=2" %%a in ('"netsh interface ipv4 show addresses | findstr /i "192.168""') do set WINIP=%%a

if defined WINIP (
    echo Found IP: %WINIP%
) else (
    echo Using default IP: 192.168.250.208
    set WINIP=192.168.250.208
)

echo.
echo Starting server at: http://%WINIP%:6000
echo.

REM Start the server
python app.py %WINIP% 6000
