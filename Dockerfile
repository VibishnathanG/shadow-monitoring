FROM python:3.12-slim

# Prevent interactive prompts during apt install
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies for Qt6 / PySide6 / X11 / OpenGL
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libegl1 \
    libxkbcommon-x11-0 \
    libdbus-1-3 \
    libxcb-cursor0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-xfixes0 \
    libxcb-xinerama0 \
    libxcb-xkb1 \
    libxrender1 \
    libxi6 \
    libxtst6 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency specifications
COPY requirements.txt .

# Install Python requirements
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir pynvml

# Copy application source code
COPY . .

# Set environment variables for Qt X11 forwarding
ENV QT_X11_NO_MITSHM=1
ENV PYTHONUNBUFFERED=1

# Execute app
CMD ["python", "app.py"]
