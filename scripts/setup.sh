#!/usr/bin/env bash
# Create the virtual environment and install dependencies (idempotent).
# Usage: bash scripts/setup.sh
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -d .venv ]; then
    if command -v python3 >/dev/null 2>&1; then
        python3 -m venv .venv
    else
        python -m venv .venv
    fi
fi

# Windows venvs have Scripts/, POSIX venvs have bin/
if [ -x .venv/Scripts/python.exe ]; then
    PY=.venv/Scripts/python.exe
else
    PY=.venv/bin/python
fi

"$PY" -m pip install --upgrade pip
"$PY" -m pip install -r requirements.txt -r requirements-dev.txt
echo "setup done: $("$PY" --version)"
