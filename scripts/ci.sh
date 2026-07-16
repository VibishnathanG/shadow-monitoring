#!/bin/bash
set -e

cd "$(dirname "$0")/.."

echo "==================================="
echo "  Shadow Monitor CI Build (Linux)  "
echo "==================================="

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "Detected OS: $NAME"
fi

./scripts/clean.sh

if [ ! -f "venv/bin/activate" ]; then
    echo "Creating virtual environment..."
    rm -rf venv
    python3 -m venv venv
fi

source venv/bin/activate
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

echo "Running PyInstaller..."
pyinstaller ShadowMonitor.spec --clean -y

echo "==================================="
echo " Build successful!                 "
echo " Artifacts are in dist/            "
echo "==================================="
