#!/bin/bash

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null
then
    echo "PyInstaller could not be found"
    echo "Installing PyInstaller..."
    pip install pyinstaller
else
    echo "PyInstaller is installed"
fi

# Build the exe from the .spec file
pyinstaller task_manager.spec

echo "Build completed!"