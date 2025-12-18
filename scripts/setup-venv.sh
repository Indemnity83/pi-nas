#!/bin/bash
# Setup shared Python virtual environment for NAS services

set -e

cd "$(dirname "$0")/.."  # Go to project root

echo "Setting up Python virtual environment..."

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv --system-site-packages
    echo "✓ Created virtual environment (with system packages)"
else
    echo "✓ Virtual environment already exists"
fi

# Activate and install/update packages
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "✓ Installed Python dependencies"
echo ""
echo "Installed packages:"
pip list | grep -E "(glances|pillow|luma|requests|RPi.GPIO)"
