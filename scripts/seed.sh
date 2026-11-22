#!/usr/bin/env bash
# Apply pending migrations and load synthetic seed data (idempotent).
# Usage: bash scripts/seed.sh
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -x .venv/Scripts/python.exe ]; then
    PY=.venv/Scripts/python.exe
else
    PY=.venv/bin/python
fi

"$PY" manage.py migrate --noinput
"$PY" scripts/seed.py
