import os
import sys
import shutil
from cx_Freeze import setup, Executable

# Clean previous builds
if os.path.exists("build"):
    shutil.rmtree("build")
if os.path.exists("dist"):
    shutil.rmtree("dist")

# Dependencies
build_exe_options = {
    "packages": ["os", "tkinter", "psutil", "PIL", "tqdm", "colorama"],
    "excludes": [],
    "include_files": [
        "requirements.txt",
        "LICENSE",
        "README.md",
        "screenshots"
    ],
    "include_msvcr": True,
}

# Base for Windows GUI
base = None
if sys.platform == "win32":
    base = "Win32GUI"

# Create executable
setup(
    name="Deduplicationator 3000",
    version="1.0",
    description="A futuristic GUI application for finding and removing duplicate files",
    options={
        "build_exe": build_exe_options,
        "build_exe_options": {
            "build_exe": "dist/Deduplicationator3000",
        }
    },
    executables=[
        Executable(
            "cleanup_duplicates.py",
            base=base,
            target_name="Deduplicationator3000.exe",
            icon="icon.ico" if os.path.exists("icon.ico") else None
        )
    ]
)

# Create installer
print("Building installer...")
inno_setup_path = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not os.path.exists(inno_setup_path):
    inno_setup_path = r"C:\Program Files\Inno Setup 6\ISCC.exe"

if os.path.exists(inno_setup_path):
    os.system(f'"{inno_setup_path}" installer.iss')
else:
    print("Error: Inno Setup not found. Please install Inno Setup 6 from https://jrsoftware.org/isdl.php")
    sys.exit(1)

print("Build complete! Check the 'dist' folder for the installer.") 