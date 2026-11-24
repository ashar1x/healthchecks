#!/usr/bin/env bash
# Start the development server at http://localhost:8000
# Usage: bash scripts/start.sh     (stop with Ctrl+C)
# Run scripts/reset.sh first if the database does not exist yet.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -x .venv/Scripts/python.exe ]; then
    PY=.venv/Scripts/python.exe
else
    PY=.venv/bin/python
fi

if [ ! -f hc.sqlite ]; then
    echo "hc.sqlite not found - run: bash scripts/reset.sh" >&2
    exit 1
fi

exec "$PY" manage.py runserver 127.0.0.1:8000
