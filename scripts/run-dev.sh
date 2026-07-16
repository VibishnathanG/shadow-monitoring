#!/bin/bash
set -e

cd "$(dirname "$0")/.."

if [ ! -f "venv/bin/activate" ]; then
    echo "Creating virtual environment..."
    rm -rf venv
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt

echo "Starting Shadow Monitor in dev mode..."
python app.py
