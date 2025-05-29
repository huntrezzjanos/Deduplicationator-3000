import sys
from cx_Freeze import setup, Executable
import os

# Dependencies are automatically detected, but it might need fine tuning.
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
    "build_exe": "dist/Deduplicationator3000"  # Specify the output directory
}

# Base for Windows GUI
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="Deduplicationator 3000",
    version="1.0",
    description="A futuristic GUI application for finding and removing duplicate files",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "cleanup_duplicates.py",
            base=base,
            target_name="Deduplicationator3000.exe",
            icon="icon.ico" if os.path.exists("icon.ico") else None
        )
    ]
) 