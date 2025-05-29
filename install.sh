#!/bin/bash

echo "Installing Duplicate File Finder..."
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed! Please install Python 3.6 or higher"
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Build executable
echo "Building executable..."
python setup.py build

echo
echo "Installation complete! You can find the executable in the 'build' folder."
echo

# Make the script executable
chmod +x build/*/DuplicateFileFinder 