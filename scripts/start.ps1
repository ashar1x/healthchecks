# Start the development server at http://localhost:8000
# Usage: powershell -ExecutionPolicy Bypass -File scripts\start.ps1
# (stop with Ctrl+C). Run scripts\reset.ps1 first if hc.sqlite does not exist.
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

if (-not (Test-Path "hc.sqlite")) {
    Write-Error "hc.sqlite not found - run scripts\reset.ps1 first"
}

& ".venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000
