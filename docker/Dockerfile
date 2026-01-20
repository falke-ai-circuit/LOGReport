# LOGReport - Desktop GUI Application with noVNC Access
# This Dockerfile creates a container running the PyQt5 GUI accessible via web browser

FROM python:3.12-slim

LABEL maintainer="goranjovic55"
LABEL description="LOGReport GUI with noVNC web access"

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies for PyQt5, VNC, and noVNC
RUN apt-get update && apt-get install -y --no-install-recommends \
    # X11 and display
    xvfb \
    x11vnc \
    x11-xserver-utils \
    # Window manager
    fluxbox \
    # noVNC web interface
    novnc \
    websockify \
    # PyQt5 dependencies (updated package names for Debian 12+)
    libgl1 \
    libegl1 \
    libxkbcommon0 \
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
    # Fonts
    fonts-dejavu \
    fonts-liberation \
    # Utils
    procps \
    supervisor \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create app user for security
RUN useradd -m -s /bin/bash appuser

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src/ ./src/
COPY config/ ./config/
COPY nodes.json ./

# Create directories for logs and test data
RUN mkdir -p test_logs logs

# Copy supervisor configuration
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copy startup script
COPY docker/start.sh /start.sh
RUN chmod +x /start.sh

# Set environment variables for display
ENV DISPLAY=:1
ENV VNC_PORT=5901
ENV NOVNC_PORT=6080
ENV RESOLUTION=1280x720x24

# Expose ports
# 5901 - VNC
# 6080 - noVNC (web browser access)
EXPOSE 5901 6080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:6080/ || exit 1

# Run as root for supervisor (switches to appuser for application)
CMD ["/start.sh"]
