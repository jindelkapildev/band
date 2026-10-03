FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

# Install Virtual Display (Xvfb) and noVNC web streaming components
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb \
    x11vnc \
    novnc \
    websockify \
    python3-pip \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Grant execute permissions to startup script
RUN chmod +x start.sh

CMD ["./start.sh"]
