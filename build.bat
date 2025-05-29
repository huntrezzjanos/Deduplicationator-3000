@echo off
echo Building Deduplicationator 3000...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed! Please install Python 3.6 or higher from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if Inno Setup is installed
if not exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    echo Inno Setup 6 is not installed! Please install it from https://jrsoftware.org/isdl.php
    pause
    exit /b 1
)

REM Clean previous builds
echo Cleaning previous builds...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

REM Create necessary directories
echo Creating directories...
mkdir "dist" 2>nul
mkdir "dist\Deduplicationator3000" 2>nul

REM Install required packages
echo Installing required packages...
pip install cx_Freeze pillow psutil tqdm colorama

REM Build the executable
echo Building executable...
python setup.py build

REM Create installer
echo Creating installer...
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss

echo.
echo If the build was successful, you can find the installer in the 'dist' folder.
echo The installer will be named 'Deduplicationator3000-Setup.exe'
echo.
pause 