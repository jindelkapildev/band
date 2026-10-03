#!/bin/bash

# 1. Clean up stale X11 lock files from container restarts
rm -f /tmp/.X99-lock

# 2. Start virtual display buffer
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99

# 3. Wait 2 seconds for Xvfb to initialize
sleep 2

# 4. Start Fluxbox Window Manager (enables mouse clicks and focus)
fluxbox &

# 5. Start VNC server
x11vnc -display :99 -forever -shared -nopw -rfbport 5900 &

# 6. Bind noVNC to Render PORT
PORT=${PORT:-10000}
websockify --web=/usr/share/novnc/ $PORT localhost:5900 &

# 7. Launch Python script
python3 band.py
