#!/bin/bash
# Install system dependencies
apt-get update
apt-get install -y ffmpeg

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
playwright install-deps chromium

# Install yt-dlp
pip install yt-dlp
