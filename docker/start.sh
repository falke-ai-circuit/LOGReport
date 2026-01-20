#!/bin/bash
set -e

# Display configuration
export DISPLAY=:1
RESOLUTION=${RESOLUTION:-1280x720x24}
VNC_PORT=${VNC_PORT:-5901}
NOVNC_PORT=${NOVNC_PORT:-6080}

echo "=== LOGReport noVNC Container Starting ==="
echo "Display: $DISPLAY"
echo "Resolution: $RESOLUTION"
echo "VNC Port: $VNC_PORT"
echo "noVNC Port: $NOVNC_PORT"

# Start Xvfb (virtual framebuffer)
echo "Starting Xvfb..."
Xvfb $DISPLAY -screen 0 $RESOLUTION &
XVFB_PID=$!

# Wait for X server to be ready (check if Xvfb process is running)
echo "Waiting for X server..."
sleep 3

# Verify Xvfb is running
if ! kill -0 $XVFB_PID 2>/dev/null; then
    echo "ERROR: Xvfb failed to start"
    exit 1
fi
echo "X server started successfully"

# Start fluxbox window manager
echo "Starting Fluxbox window manager..."
fluxbox &
sleep 1

# Start x11vnc server
echo "Starting VNC server on port $VNC_PORT..."
x11vnc -display $DISPLAY -forever -shared -rfbport $VNC_PORT -nopw -xkb &
sleep 2

# Start noVNC webserver using novnc_proxy for better compatibility
echo "Starting noVNC on port $NOVNC_PORT..."
/usr/share/novnc/utils/novnc_proxy --vnc localhost:$VNC_PORT --listen $NOVNC_PORT &
sleep 2

echo ""
echo "============================================"
echo "LOGReport is ready!"
echo "============================================"
echo ""
echo "Access via web browser:"
echo "  - http://localhost:$NOVNC_PORT/vnc.html"
echo "  - For Codespaces: Use the forwarded port URL + /vnc.html"
echo ""
echo "Starting LOGReport application..."
echo ""

# Change to app directory and run the application
cd /app/src

# Run the PyQt5 application
exec python main.py --gui
