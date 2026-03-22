#!/bin/bash
# Malaysia Stock Dashboard - Startup Script

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_PY="$SCRIPT_DIR/../venv/bin/python"

echo "🚀 Starting Malaysia Stock Dashboard..."
echo "📍 Open your browser to: http://localhost:6000"
echo ""

$VENV_PY $SCRIPT_DIR/app.py
