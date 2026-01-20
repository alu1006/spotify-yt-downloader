#!/bin/bash
set -e

# Install system dependencies
apt-get update
apt-get install -y ffmpeg nodejs npm

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
playwright install-deps chromium

# Install yt-dlp (latest version)
pip install --upgrade yt-dlp
