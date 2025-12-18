#!/bin/bash
# Auto-update script for OLED display
# Add to crontab: */5 * * * * /home/pi/pi-nas/scripts/update-oled.sh >> /home/pi/oled-update.log 2>&1

cd /home/pi/pi-nas

# Fetch latest from GitHub
git fetch origin main

# Check if behind
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u})

if [ "$LOCAL" != "$REMOTE" ]; then
    echo "$(date): Updates found, pulling and restarting..."
    git pull origin main

    # Update venv if requirements changed
    if git diff --name-only $LOCAL $REMOTE | grep -q requirements.txt; then
        echo "$(date): Updating virtual environment..."
        source venv/bin/activate
        pip install -r requirements.txt
    fi

    sudo systemctl restart oled-status
    echo "$(date): Deployed successfully"
else
    echo "$(date): Already up to date"
fi
