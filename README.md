# Pi NAS

Home NAS built with Raspberry Pi 4, featuring real-time OLED status display with audible alerts.

## Features

- 🗄️ **RAID 1 Storage** - Software RAID with mdadm
- 📊 **Real-time OLED Display** - Shows RAID status, temps, network, storage
- 🔔 **Audible Alerts** - Piezo buzzer alerts for degraded arrays and critical temps
- 📁 **File Sharing** - Samba network shares
- 📈 **System Monitoring** - Glances web interface
- 🖨️ **3D Printed Enclosure** - Custom designed case

## Hardware

- Raspberry Pi 4 (4GB+)
- 2x HDDs for RAID 1
- 128x64 I2C OLED Display (SSD1306)
- Piezo buzzer module
- Momentary push button

## Project Structure

```
pi-nas/
├── oled-status/          # OLED status display application
├── config/               # System configuration files
│   └── systemd/         # Service definitions
├── scripts/              # Setup and maintenance scripts
├── hardware/             # 3D models and wiring diagrams
└── docs/                 # Documentation
```

## Quick Start

### On the Pi

1. **Clone the repository:**
   ```bash
   cd ~
   git clone https://github.com/yourusername/pi-nas.git
   cd pi-nas
   ```

2. **Setup Python environment:**
   ```bash
   chmod +x scripts/setup-venv.sh
   ./scripts/setup-venv.sh
   ```

3. **Install services:**
   ```bash
   chmod +x scripts/install-services.sh
   ./scripts/install-services.sh
   ```

4. **Start services:**
   ```bash
   sudo systemctl start glances.service
   sudo systemctl start oled-status.service
   ```

## OLED Status Display

The OLED display shows different pages based on system state:

- **Online** - Normal operation showing storage usage, I/O, and temps
- **Resync/Recovery/Check/Repair** - Progress and ETA for RAID operations
- **DEGRADED** - Warning display when array is degraded

Navigate pages with the button. Auto-returns to home after 10 seconds of inactivity.

### Alarm Conditions

Audible alerts via piezo buzzer:
- RAID degraded or resyncing
- Disk temperature ≥50°C (warning) or ≥60°C (critical)
- Bad SMART sectors detected
- CPU under-voltage or throttling

## Development

Developed on Mac, deployed to Pi via git.

### Update Deployment

From your Mac:
```bash
git add -A
git commit -m "Update feature"
git push
```

On Pi, updates can be automatic (see `scripts/update-oled.sh`) or manual:
```bash
cd ~/pi-nas
git pull
sudo systemctl restart oled-status
```

## License

MIT
