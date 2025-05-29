@echo off
echo Installing Duplicate File Finder...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed! Please install Python 3.6 or higher from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

REM Install requirements
echo Installing requirements...
pip install -r requirements.txt

REM Build executable
echo Building executable...
python setup.py build

echo.
echo Installation complete! You can find the executable in the 'build' folder.
echo.
pause 