#!/bin/bash
set -e

cd "$(dirname "$0")/.."

echo "Creating release package..."
./scripts/ci.sh

mkdir -p release
cp dist/ShadowMonitor* release/ 2>/dev/null || true
cp README.md release/
cp LICENSE release/ 2>/dev/null || echo "No LICENSE found."
cp CHANGELOG.md release/ 2>/dev/null || echo "No CHANGELOG found."

echo "Release package created in release/"
