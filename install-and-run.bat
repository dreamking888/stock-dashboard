@echo off
echo ========================================
echo   Malaysia Stock Dashboard - Auto Install
echo ========================================
echo.

REM Check if Python exists
python --version >nul 2>&1
if not errorlevel 1 goto :run

echo Python not found. Installing...

REM Download and install Python silently
echo Downloading Python...
powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe' -OutFile 'C:\temp_python_installer.exe'"

echo Installing Python (this may take a minute)...
start /wait C:\temp_python_installer.exe /quiet InstallAllUsers=1 PrependPath=1

echo Cleaning up...
del C:\temp_python_installer.exe

REM Refresh environment
set PATH=C:\Python312;C:\Python312\Scripts;%PATH%

:run
echo.
echo Starting Dashboard...
echo.

python app.py 192.168.250.208 6000
