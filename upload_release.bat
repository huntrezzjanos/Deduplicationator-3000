@echo off
echo Uploading Deduplicationator 3000 Release...

REM Check if GitHub CLI is installed
gh --version >nul 2>&1
if errorlevel 1 (
    echo GitHub CLI is not installed! Please install it from https://cli.github.com/
    pause
    exit /b 1
)

REM Create release
echo Creating release...
gh release create v1.0 ^
    --title "Deduplicationator 3000 v1.0" ^
    --notes-file RELEASE_NOTES.md ^
    "dist\Deduplicationator3000-Setup.exe"

echo.
echo If the upload was successful, you can find the release at:
echo https://github.com/huntrezzjanos/Deduplicationator-3000/releases
echo.
pause 