#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "========================================================"
echo " Launching Retinal Fundus Multi-Task Assessment App"
echo "========================================================"
echo ""

if [ -f "../cvd-env/bin/python" ]; then
    echo "Using python from ../cvd-env/bin/python"
    ../cvd-env/bin/python app.py
elif [ -f "venv/bin/python" ]; then
    echo "Using python from venv/bin/python"
    venv/bin/python app.py
elif command -v python3 &>/dev/null; then
    echo "Using python3..."
    python3 app.py
else
    echo "Using python..."
    python app.py
fi
