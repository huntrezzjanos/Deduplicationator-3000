@echo off
echo Installing Duplicate File Finder...

REM Create virtual environment in the current directory
echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo Failed to create virtual environment. Please ensure Python is installed and you have write permissions.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Failed to activate virtual environment.
    pause
    exit /b 1
)

REM Install requirements
echo Installing requirements...
pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install requirements.
    pause
    exit /b 1
)

REM Build executable
echo Building executable...
python setup.py build
if errorlevel 1 (
    echo Failed to build executable.
    pause
    exit /b 1
)

echo Installation complete! You can find the executable in the 'build' folder.
pause 