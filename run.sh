#!/usr/bin/env bash

# Resolve script folder and change directory
cd "$(dirname "$0")"

echo "=================================================="
echo "         Launching Shadow System Monitor          "
echo "=================================================="

# 1. Parse .env file
VENV_PATH=""
if [ -f .env ]; then
    # Extract VENV_PATH value, removing any quotes
    VENV_PATH=$(grep -E "^\s*VENV_PATH\s*=" .env | cut -d'=' -f2- | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e 's/^["'\''\(]*//' -e 's/["'\''\)]*$//')
fi

# 2. Activate Virtual Environment
if [ -n "$VENV_PATH" ]; then
    if [ -f "$VENV_PATH/bin/activate" ]; then
        echo "[VENV] Activating virtual environment: $VENV_PATH/bin/activate"
        source "$VENV_PATH/bin/activate"
    elif [ -f "$VENV_PATH/Scripts/activate" ]; then
        echo "[VENV] Activating virtual environment: $VENV_PATH/Scripts/activate"
        source "$VENV_PATH/Scripts/activate"
    else
        echo "[WARNING] Activation script not found in $VENV_PATH"
        echo "[WARNING] Running with system default Python environment..."
    fi
else
    echo "[INFO] VENV_PATH not defined in .env. Running with default system Python..."
fi

# 3. Start Application
echo "[APP] Starting Shadow Monitor..."
python app.py

echo "Shadow Monitor closed."
