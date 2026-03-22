@echo off
echo ========================================
echo   Malaysia Stock Dashboard
echo ========================================
echo.

REM Try to find Python (multiple methods)
set PYTHON=

REM Method 1: Check py launcher
py --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON=py
    goto :found
)

REM Method 2: Check python directly
python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON=python
    goto :found
)

REM Method 3: Check common installation paths
if exist "C:\Python312\python.exe" set PYTHON=C:\Python312\python.exe
if exist "C:\Python311\python.exe" set PYTHON=C:\Python311\python.exe
if exist "C:\Python310\python.exe" set PYTHON=C:\Python310\python.exe
if exist "C:\Program Files\Python312\python.exe" set PYTHON="C:\Program Files\Python312\python.exe"
if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe" set PYTHON="C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe"

if defined PYTHON goto :found

echo ERROR: Python not found!
echo.
echo Please install Python from https://www.python.org/downloads/
echo Make sure to check "Add Python to PATH"
echo.
pause
exit /b 1

:found
echo Found Python: %PYTHON%
echo.

REM Install dependencies if needed
%PYTHON% -m pip show flask >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    %PYTHON% -m pip install flask flask-cors yfinance pandas numpy
    echo.
)

REM Detect IP or use default
set HOST=192.168.250.208
for /f "delims= tokens=2" %%a in ('"netsh interface ipv4 show addresses | findstr /i "192.168""') do set HOST=%%a

echo ========================================
echo   Starting Dashboard
echo   URL: http://%HOST%:6000
echo ========================================
echo.
echo Press CTRL+C to stop
echo.

REM Start server
%PYTHON% app.py %HOST% 8888
