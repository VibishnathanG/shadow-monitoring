@echo off
:: Batch Launcher for Shadow System Monitor
:: Bypasses Windows PowerShell signature restrictions natively

set SCRIPT_DIR=%~dp0
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%run.ps1"
