#!/bin/bash
# Install systemd services for NAS

set -e

cd "$(dirname "$0")/.."

echo "Installing systemd services..."

# Copy service files
sudo cp config/systemd/*.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable glances.service
sudo systemctl enable oled-status.service

echo "✓ Services installed and enabled"
echo ""
echo "To start services now, run:"
echo "  sudo systemctl start glances.service"
echo "  sudo systemctl start oled-status.service"
echo ""
echo "To check status:"
echo "  systemctl status glances.service"
echo "  systemctl status oled-status.service"
