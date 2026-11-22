#!/usr/bin/env bash
# Reset the database to a clean, seeded state.
# Usage: bash scripts/reset.sh
# Stop the development server first (Ctrl+C): Windows locks hc.sqlite while
# runserver holds it open, so deletion fails with a clear error if it is running.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -x .venv/Scripts/python.exe ]; then
    PY=.venv/Scripts/python.exe
else
    PY=.venv/bin/python
fi

if [ -f hc.sqlite ]; then
    echo "removing hc.sqlite (stop the server first if this fails)"
    rm hc.sqlite
fi

"$PY" manage.py migrate --noinput
"$PY" scripts/seed.py
echo "reset complete"
