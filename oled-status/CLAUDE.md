# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Raspberry Pi system monitor that displays real-time stats on a 128x64 OLED display (SSD1306). Shows CPU, memory, network, RAID status, storage, and temperatures with button navigation.

## Architecture

**Single-file application** (`oled-status.py`) organized into functional sections:

- **Configuration (lines 20-82)**: Hardware pins, timing intervals, screen dimensions, fonts
- **Icon rendering (lines 127-383)**: Animated pixel patterns for RAID states (clean, rebuilding, degraded) and power warnings
- **Data gathering (lines 390-850)**: Fetches from Glances API (localhost:61208), reads `/proc/mdstat` for RAID, queries vcgencmd for Pi hardware
- **Display rendering (lines 852-1170)**: Page renderers for different views (network, system, storage, RAID, temps)
- **Navigation (lines 1172-1212)**: GPIO button handler cycles through pages, auto-returns to home after 10s timeout
- **Main loop (lines 1213-1299)**: Refreshes data every 2s, redraws OLED every 0.2s

**Key state variables** (lines 122-125):
- `LAST_DATA`: Cached system metrics
- `current_page`: -1 for home mode, 0-4 for detail pages
- `SPIN_FRAME`: 0-3 animation counter
- `MD_NAME`: Auto-detected RAID device (e.g., "md127")

**Home mode logic** (lines 1202-1207):
- Shows large animated icon with stats
- `page_clean()` for normal operation
- `page_resync()` during RAID rebuild with progress bar

## Data Sources

- **Glances API** (`http://localhost:61208/api/4`): CPU, memory, network, disk I/O, SMART temps
- **System files**: `/proc/mdstat`, `/proc/mounts`, `/sys/block/*/md/*` for RAID state
- **Raspberry Pi tools**: `vcgencmd` for CPU temp and power throttling

## Display Layout

- **Header** (top 16px): Page title + power warning icon
- **Body** (48px): Three 14px lines (L1/L2/L3) or large icon + stats

## Development

Run directly on Raspberry Pi with I2C and GPIO access:
```bash
sudo python3 oled-status.py
```

**Dependencies**: RPi.GPIO, luma.oled, PIL, requests

**Debug mode** (line 1279): Set `DEBUG_PAGE = page_network` to test specific pages without navigation

## Common Modifications

**Adjust font paths** (lines 47-49): Update if FiraCode is in different location
**Change RAID mount** (line 390): Modify `prefer_mountpoint` if storage isn't at `/mnt/storage`
**Add new pages**: Create `page_*` function, add to `PAGE_FUNCS` list (line 1200)
**Customize timing**: Edit `NAV_TIMEOUT`, `DATA_INTERVAL`, `DISPLAY_INTERVAL` (lines 31-33)

## Font Rendering

Uses dynamic column calculation (lines 69-82) to fit text based on actual font metrics. All text formatting respects `BODY_COLS` and `HEADER_COLS` for alignment.

Helper functions:
- `fmt_label_value()`: Auto-space between label and right-aligned value
- `draw_label_value()`: Pixel-accurate rendering
- `fmt_two_cols()`: Split screen for dual metrics (e.g., TX/RX rates)
