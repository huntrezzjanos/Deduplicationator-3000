import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    "packages": ["os", "tkinter", "psutil", "tqdm", "colorama"],
    "excludes": [],
    "include_files": []
}

base = None
if sys.platform == "win32":
    base = "Win32GUI"  # Use this for Windows GUI applications

setup(
    name="Duplicate File Finder",
    version="1.0",
    description="Find and remove duplicate files easily",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "cleanup_duplicates.py",
            base=base,
            target_name="DuplicateFileFinder.exe",
            icon="icon.ico"  # You'll need to add an icon file
        )
    ]
) 