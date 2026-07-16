$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -Path "$scriptDir\.."

Write-Host "Creating release package..." -ForegroundColor Cyan
.\scripts\ci.ps1

if (-Not (Test-Path "release")) {
    New-Item -ItemType Directory -Path "release" | Out-Null
}

if (Test-Path "dist\ShadowMonitor.exe") {
    Copy-Item "dist\ShadowMonitor.exe" "release\" -Force
}
if (Test-Path "README.md") {
    Copy-Item "README.md" "release\" -Force
}
if (Test-Path "LICENSE") {
    Copy-Item "LICENSE" "release\" -Force
}
if (Test-Path "CHANGELOG.md") {
    Copy-Item "CHANGELOG.md" "release\" -Force
}

Write-Host "Release package created in release\" -ForegroundColor Green
