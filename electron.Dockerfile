FROM node:18-alpine

# Install required packages for Electron
RUN apk add --no-cache \
    xvfb \
    gtk+3.0-dev \
    libxss1 \
    gconf-service \
    libasound2 \
    libatk1.0-0 \
    libc6 \
    libcairo-gobject2 \
    libdrm2 \
    libgtk-3-0 \
    libgdk-pixbuf2.0-0

WORKDIR /app

# Copy frontend package files
COPY frontend/package*.json ./frontend/

# Install frontend dependencies
WORKDIR /app/frontend
RUN npm ci

# Install Quasar CLI globally
RUN npm install -g @quasar/cli

# Copy application files
COPY frontend/ ./
COPY electron/ ../electron/
COPY dist/ ../dist/

# Back to app root
WORKDIR /app

# Expose display for X11
ENV DISPLAY=:0

# Run Electron in development mode
CMD ["quasar", "dev", "-m", "electron"]