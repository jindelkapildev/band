#!/bin/bash

# Start virtual display buffer
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99

# Start VNC server on display :99
x11vnc -display :99 -forever -shared -nopw -rfbport 5900 &

# Bind noVNC to Render's dynamic PORT (defaults to 10000 if PORT is unset)
PORT=${PORT:-10000}
websockify --web=/usr/share/novnc/ $PORT localhost:5900 &

# Launch Python automation script
python3 band.py
