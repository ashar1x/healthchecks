# Apply pending migrations and load synthetic seed data (idempotent).
# Usage: powershell -ExecutionPolicy Bypass -File scripts\seed.ps1
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

& ".venv\Scripts\python.exe" manage.py migrate --noinput
& ".venv\Scripts\python.exe" scripts\seed.py
