$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -Path "$scriptDir\.."

Write-Host "===================================" -ForegroundColor Cyan
Write-Host "  Shadow Monitor CI Build (Win)    " -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan

.\scripts\clean.ps1

if (-Not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "Creating virtual environment..."
    if (Test-Path "venv") {
        Remove-Item -Recurse -Force "venv"
    }
    python -m venv venv
}

.\venv\Scripts\Activate.ps1
Write-Host "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

Write-Host "Running PyInstaller..."
pyinstaller ShadowMonitor.spec --clean -y

if ($LASTEXITCODE -eq 0) {
    Write-Host "===================================" -ForegroundColor Green
    Write-Host " Build successful!                 " -ForegroundColor Green
    Write-Host " Artifacts are in dist\            " -ForegroundColor Green
    Write-Host "===================================" -ForegroundColor Green
} else {
    Write-Host "Build failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}
