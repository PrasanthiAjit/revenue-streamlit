#!/usr/bin/env bash
set -euo pipefail
# run.sh - convenience launcher for the Streamlit app
# Usage: ./run.sh [streamlit args]

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$ROOT_DIR/.venv"
APP="$ROOT_DIR/app.py"

# Prefer the venv's streamlit if available
if [ -x "$VENV/bin/streamlit" ]; then
  STREAMLIT_CMD="$VENV/bin/streamlit"
elif command -v streamlit >/dev/null 2>&1; then
  STREAMLIT_CMD="$(command -v streamlit)"
elif [ -x "$VENV/bin/python" ]; then
  STREAMLIT_CMD="$VENV/bin/python -m streamlit"
else
  STREAMLIT_CMD="python -m streamlit"
fi

echo "Starting Streamlit with: $STREAMLIT_CMD run $APP $*"
# Use eval so the command string can include "python -m streamlit"
eval "$STREAMLIT_CMD run \"$APP\" $*"
