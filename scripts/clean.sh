#!/bin/bash
set -e

echo "Cleaning build artifacts..."
cd "$(dirname "$0")/.."

rm -rf build/ dist/ release/
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

echo "Clean complete."
