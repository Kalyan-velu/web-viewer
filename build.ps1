# Check if PyInstaller is installed
if (!(pip list | Select-String "pyinstaller"))
{
    Write-Host "PyInstaller could not be found"
    Write-Host "Installing PyInstaller..."
    pip install pyinstaller
}
else
{
    Write-Host "PyInstaller is installed"
}

# Build the exe from the .spec file
pyinstaller --clean crawler.spec

Write-Host "Build completed!"