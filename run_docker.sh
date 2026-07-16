#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "===================================================="
echo "    Launching Shadow System Monitor in Docker  "
echo "===================================================="

# 1. Authorize local container connections to host X11 server (Linux)
if command -v xhost &>/dev/null; then
  echo "[X11] Authorizing local docker access..."
  xhost +local:root
else
  echo "[X11] xhost command not found. Skipping X11 authorization..."
fi

# 2. Export Host Display
if [ -z "$DISPLAY" ]; then
  export DISPLAY=:0
  echo "[DISPLAY] Defaulting to :0"
else
  echo "[DISPLAY] Using host display: $DISPLAY"
fi

# 3. Launch Docker Compose
echo "[Docker] Building and launching system monitor..."
docker compose up --build
