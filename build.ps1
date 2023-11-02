# Function to check if a browser is installed for Playwright
function IsPlaywrightBrowserInstalled($browserName) {
    $output = playwright show $browserName 2>&1
    return ($output -notlike "Unknown browser*")
}

# Check if browsers are installed for Playwright
$requiredBrowsers = @("chromium", "firefox", "webkit")  # Add other browsers as needed

foreach ($browser in $requiredBrowsers) {
    if (-Not (IsPlaywrightBrowserInstalled $browser)) {
        Write-Host "$browser is not installed for Playwright."
        Write-Host "Installing $browser..."
        playwright install $browser
    } else {
        Write-Host "$browser is installed for Playwright"
    }
}

# Check if PyInstaller is installed
if (!(Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    Write-Host "PyInstaller could not be found"
    Write-Host "Installing PyInstaller..."
    pip install pyinstaller
} else {
    Write-Host "PyInstaller is installed"
}

# Build the exe from the .spec file
pyinstaller --clean crawler.spec

Write-Host "Build completed!"