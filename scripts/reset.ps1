# Reset the database to a clean, seeded state.
# Usage: powershell -ExecutionPolicy Bypass -File scripts\reset.ps1
# Stop the development server first (Ctrl+C): Windows locks hc.sqlite while
# runserver holds it open, so deletion fails if the server is still running.
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

if (Test-Path "hc.sqlite") {
    Write-Host "removing hc.sqlite (stop the server first if this fails)"
    Remove-Item "hc.sqlite"
}

& ".venv\Scripts\python.exe" manage.py migrate --noinput
& ".venv\Scripts\python.exe" scripts\seed.py
Write-Host "reset complete"
