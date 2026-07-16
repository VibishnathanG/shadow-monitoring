$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -Path "$scriptDir\.."

if (-Not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "Creating virtual environment..."
    if (Test-Path "venv") {
        Remove-Item -Recurse -Force "venv"
    }
    python -m venv venv
}

.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

Write-Host "Starting Shadow Monitor in dev mode..." -ForegroundColor Green
python app.py
