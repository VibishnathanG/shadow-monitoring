# PowerShell Startup Script for Shadow System Monitor
# Parses environment variables from .env and executes dynamically

# 1. Navigate to script location (supports UNC paths, local drives, etc.)
Set-Location $PSScriptRoot

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "         Launching Shadow System Monitor          " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 2. Parse .env file
$EnvFile = Join-Path $PSScriptRoot ".env"
$VenvPath = ""
if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        # Match lines starting with VENV_PATH=
        if ($_ -match "^\s*VENV_PATH\s*=\s*(.+)") {
            $VenvPath = $Matches[1].Trim().Trim('"').Trim("'")
        }
    }
}

# 3. Activate Virtual Environment
if ($VenvPath) {
    $WindowsActivate = Join-Path $VenvPath "Scripts\Activate.ps1"
    if (Test-Path $WindowsActivate) {
        Write-Host "[VENV] Activating virtual environment: $WindowsActivate" -ForegroundColor Green
        . $WindowsActivate
        
        # Auto-verify and install dependencies in the activated venv
        $PythonExe = Join-Path $VenvPath "Scripts\python.exe"
        if (Test-Path $PythonExe) {
            Write-Host "[PIP] Auto-verifying/installing requirements inside virtual environment..." -ForegroundColor Green
            & $PythonExe -m pip install -r "$PSScriptRoot\requirements.txt" --quiet
        }
    } else {
        Write-Host "[WARNING] Activation script not found at: $WindowsActivate" -ForegroundColor Yellow
        Write-Host "[WARNING] Running with system default Python environment..." -ForegroundColor Yellow
    }
} else {
    Write-Host "[INFO] VENV_PATH not defined in .env. Running with default system Python..." -ForegroundColor Gray
}

# 4. Start Application
Write-Host "[APP] Starting Shadow Monitor..." -ForegroundColor Green
python app.py

Write-Host "Shadow Monitor closed." -ForegroundColor Cyan
