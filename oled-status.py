#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time
import socket
import subprocess
import signal
from datetime import datetime
import re
import sys
import math
import os
import glob

import requests
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont

# -------------------------
# External services / hardware
# -------------------------

GLANCES_URL = "http://localhost:61208/api/4"
I2C_ADDRESS = 0x3C
BUTTON_PIN = 4

# -------------------------
# Timing / behavior
# -------------------------

NAV_TIMEOUT = 10.0         # seconds before auto-return to "home" page
DATA_INTERVAL = 2.0        # seconds between Glances polls
DISPLAY_INTERVAL = 0.2     # seconds between OLED refreshes

# -------------------------
# Screen geometry
# -------------------------

SCREEN_W = 128
SCREEN_H = 64

# -------------------------
# Fonts
# -------------------------

try:
    FONT = ImageFont.truetype(
        "/usr/share/fonts/truetype/firacode/FiraCode-Regular.ttf", 12
    )
    HEADER_FONT = ImageFont.truetype(
        "/usr/share/fonts/truetype/firacode/FiraCode-Bold.ttf", 13
    )
except OSError:
    FONT = ImageFont.load_default()
    HEADER_FONT = ImageFont.load_default()

# -------------------------
# Font metrics
# -------------------------

def text_width(font, s: str) -> int:
    try:
        return math.ceil(font.getlength(s))
    except AttributeError:
        # Pillow fallback
        bbox = font.getbbox(s)
        return bbox[2] - bbox[0]

def compute_cols_fit(screen_w: int, font, sample_char: str = "0") -> int:
    # Find max N such that N sample chars fit in screen_w
    lo, hi = 1, 64  # plenty for 128px wide OLED
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if text_width(font, sample_char * mid) <= screen_w:
            lo = mid
        else:
            hi = mid - 1
    return lo


BODY_COLS = compute_cols_fit(SCREEN_W, FONT)
HEADER_COLS = compute_cols_fit(SCREEN_W, HEADER_FONT)

# -------------------------
# Header layout
# -------------------------

HEADER_HEIGHT = 16

HEADER_TEXT_X = 0
HEADER_TEXT_Y = 0

HEADER_RIGHT_PADDING = 2
HEADER_ICON_SIZE = 14
HEADER_ICON_Y = (HEADER_HEIGHT - HEADER_ICON_SIZE) // 2
HEADER_ICON_X = SCREEN_W - HEADER_ICON_SIZE - HEADER_RIGHT_PADDING

# -------------------------
# Body layout
# -------------------------

BODY_TOP = HEADER_HEIGHT
BODY_HEIGHT = SCREEN_H - HEADER_HEIGHT

BODY_CENTER_Y = BODY_TOP + (BODY_HEIGHT // 2)

LINE_HEIGHT = 14
BODY_TEXT_LINES = 3
BODY_TEXT_HEIGHT = LINE_HEIGHT * BODY_TEXT_LINES

BODY_ICON_SIZE = 28
BODY_ICON_Y = BODY_CENTER_Y - (BODY_ICON_SIZE // 2)

L1 = BODY_CENTER_Y - (BODY_TEXT_HEIGHT // 2)
L2 = L1 + LINE_HEIGHT
L3 = L2 + LINE_HEIGHT

# -------------------------
# Runtime state
# -------------------------

LAST_DATA = {}
LAST_DATA_TS = 0.0
SPIN_FRAME = 0
MD_NAME = None

def make_icon(pattern):
    """Convert a 14x14 pattern of '.' and '#' into (x, y) coords."""
    coords = []
    for y, row in enumerate(pattern):
        for x, ch in enumerate(row):
            if ch == '#':
                coords.append((x, y))
    return coords

REBUILD_PATTERNS = [
    [   # REBUILD_FRAME_0
        "....######....",
        "...#......#...",
        "..#........#..",
        ".#...#......#.",
        "#...#........#",
        "#..#..##.....#",
        "#.#..#..#..#.#",
        "#.#..#..#..#.#",
        "#.....##..#..#",
        "#........#...#",
        ".#......#...#.",
        "..#........#..",
        "...#......#...",
        "....######....",
    ],
    [   # REBUILD_FRAME_1
        "....######....",
        "...#......#...",
        "..#...##...#..",
        ".#...#..#...#.",
        "#...#........#",
        "#.....##.....#",
        "#....#..#....#",
        "#....#..#....#",
        "#.....##.....#",
        "#........#...#",
        ".#...#..#...#.",
        "..#...##...#..",
        "...#......#...",
        "....######....",
    ],
    [   # REBUILD_FRAME_2
        "....######....",
        "...#......#...",
        "..#....#...#..",
        ".#......#...#.",
        "#........#...#",
        "#.....##..#..#",
        "#....#..#..#.#",
        "#.#..#..#....#",
        "#..#..##.....#",
        "#...#........#",
        ".#...#......#.",
        "..#...#....#..",
        "...#......#...",
        "....######....",
    ],
    [   # REBUILD_FRAME_3
        "....######....",
        "...#......#...",
        "..#........#..",
        ".#..........#.",
        "#........#...#",
        "#..#..##..#..#",
        "#.#..#..#..#.#",
        "#.#..#..#..#.#",
        "#..#..##..#..#",
        "#...#........#",
        ".#..........#.",
        "..#........#..",
        "...#......#...",
        "....######....",
    ],
]

REBUILD_FRAMES = [make_icon(p) for p in REBUILD_PATTERNS]

DEGRADED_PATTERNS = [
    [   # DEGRADED_FRAME_0
        "....######....",
        "...#......#...",
        "..#........#..",
        ".#....##....#.",
        "#.....##.....#",
        "#.....##.....#",
        "#.....##.....#",
        "#.....##.....#",
        "#............#",
        "#.....##.....#",
        ".#....##....#.",
        "..#........#..",
        "...#......#...",
        "....######....",
    ],
    [   # DEGRADED_FRAME_1
        "....######....",
        "...#......#...",
        "..#........#..",
        ".#..........#.",
        "#............#",
        "#............#",
        "#............#",
        "#............#",
        "#............#",
        "#............#",
        ".#..........#.",
        "..#........#..",
        "...#......#...",
        "....######....",
    ],
]

DEGRADED_FRAMES = [make_icon(p) for p in DEGRADED_PATTERNS]

UNKNOWN_PATTERNS = [
    [   # DEGRADED_FRAME_0
        "....######....",
        "...#......#...",
        "..#........#..",
        ".#...####...#.",
        "#...#....#...#",
        "#........#...#",
        "#........#...#",
        "#......##....#",
        "#.....#......#",
        "#.....#......#",
        ".#..........#.",
        "..#...#....#..",
        "...#......#...",
        "....######....",
    ],
    [   # DEGRADED_FRAME_1
        "....######....",
        "...#......#...",
        "..#........#..",
        ".#..........#.",
        "#............#",
        "#............#",
        "#............#",
        "#............#",
        "#............#",
        "#............#",
        ".#..........#.",
        "..#........#..",
        "...#......#...",
        "....######....",
    ],
]

UNKNOWN_FRAMES = [make_icon(p) for p in UNKNOWN_PATTERNS]

CLEAN_PATTERN = [
        "....######....",
        "..##......#.##",
        "..#.........##",
        ".#.........##.",
        "#.........##..",
        "#........##..#",
        "#...#...##...#",
        "#...##.##....#",
        "#....###.....#",
        "#.....#......#",
        ".#..........#.",
        "..#........#..",
        "...#......#...",
        "....######....",
]

CLEAN_FRAME = make_icon(CLEAN_PATTERN)

POWER_PATTERNS = [
    # [   # POWER_FRAME_0 (outline)
    #     ".....#######..",
    #     ".....#.....#..",
    #     "....#.....#...",
    #     "....#....#....",
    #     "...#....#.....",
    #     "...#...####...",
    #     "..#.......#...",
    #     "..###....#....",
    #     "....#...#.....",
    #     "...#...#......",
    #     "...#..#.......",
    #     "..#..#........",
    #     "..#.#.........",
    #     "..##..........",
    # ],
    # [   # POWER_FRAME_1 (filled)
    #     ".....#######..",
    #     ".....#######..",
    #     "....#######...",
    #     "....######....",
    #     "...######.....",
    #     "...########...",
    #     "..#########...",
    #     "..########....",
    #     "....#####.....",
    #     "...#####......",
    #     "...####.......",
    #     "..####........",
    #     "..###.........",
    #     "..##..........",
    # ],
    [   # DEGRADED_FRAME_1
        "..............",
        ".##...........",
        ".##......#....",
        ".##......#....",
        ".##....#.#.#..",
        ".##...#..#..#.",
        ".##..#...#...#",
        ".##..#.......#",
        ".##..#.......#",
        "......#.....#.",
        ".......#...#..",
        ".##.....###...",
        ".##...........",
        "..............",
    ],

    [   # DEGRADED_FRAME_1
        "..............",
        "..............",
        ".........#....",
        ".........#....",
        ".......#.#.#..",
        "......#..#..#.",
        ".....#...#...#",
        ".....#.......#",
        ".....#.......#",
        "......#.....#.",
        ".......#...#..",
        "........###...",
        "..............",
        "..............",
    ],

    # [   # DEGRADED_FRAME_1
    #     "........#.....",
    #     "##......#.....",
    #     "##....#.#.#...",
    #     "##...#..#..#..",
    #     "##..#...#...#.",
    #     "##.#.........#",
    #     "##.#.........#",
    #     "##.#.........#",
    #     "##.#.........#",
    #     "...#.........#",
    #     "....#.......#.",
    #     "##...#.....#..",
    #     "##....#####...",
    #     "..............",
    # ],
]

POWER_FRAMES = [make_icon(p) for p in POWER_PATTERNS]


# -------------------------
# Helpers
# -------------------------

def resolve_md_name(prefer_mountpoint: str = "/mnt/storage") -> str | None:
    # Best: what backs the mount
    try:
        with open("/proc/mounts") as f:
            for line in f:
                dev, mnt, *_ = line.split()
                if mnt == prefer_mountpoint:
                    base = os.path.basename(dev)
                    m = re.match(r"^(md\d+)", base)  # md127 or md127p1
                    if m:
                        return m.group(1)
    except Exception:
        pass

    # Next best: /proc/mdstat
    try:
        with open("/proc/mdstat") as f:
            for line in f:
                m = re.match(r"^(md\d+)\s*:\s*", line)
                if m:
                    return m.group(1)
    except Exception:
        pass

    # Fallback: /dev/md*
    for path in sorted(glob.glob("/dev/md[0-9]*")):
        return os.path.basename(path)

    return None

def fmt_rate(k_per_s):
    """
    Convert K/s (string or number) to human readable rate.
    Examples:
      950   -> "950K/s"
      12500 -> "12.5M/s"
      1048576 -> "1.0G/s"
    """
    try:
        k = float(k_per_s)
    except (TypeError, ValueError):
        return "N/A"

    if k < 1024:
        return f"{k:0.0f}K/s"
    elif k < 1024**2:
        return f"{k/1024:0.1f}M/s"
    else:
        return f"{k/(1024**2):0.1f}G/s"

def fmt_minutes(minutes):
   return fmt_time(minutes * 60)

def fmt_time(seconds):
    if seconds is None:
        return "N/A"

    s = int(seconds)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)

    if d > 0:
        return f"{d}d {h}h"
    elif h > 0:
        return f"{h}h {m}m"
    else:
        return f"{m}m"

def fmt_bytes(n: int | float | None) -> str:
    if n is None:
        return "N/A"
    try:
        n = float(n)
    except (TypeError, ValueError):
        return "N/A"

    units = ["B", "K", "M", "G", "T", "P"]
    i = 0
    while n >= 1024 and i < len(units) - 1:
        n /= 1024.0
        i += 1

    # no decimals for B/K, 1 decimal for M+ (tweak to taste)
    return f"{n:.0f}{units[i]}" if i < 2 else f"{n:.1f}{units[i]}"

def fmt_temp(val, *, warn=50.0, hot=60.0) -> str:
    """
    Format a temperature with visual severity markers.
    """
    if val is None:
        return "N/A"

    try:
        t = float(val)
    except (TypeError, ValueError):
        return "N/A"

    if t >= hot:
        return f"!!{t:0.1f}C"
    elif t >= warn:
        return f"! {t:0.1f}C"
    else:
        return f"  {t:0.1f}C"

def fmt_label_value(label: str, value: str) -> str:
    """
    Return one string where `label` is left-aligned and `value` is right-aligned
    within BODY_COLS characters.
    Example (BODY_COLS=21):
      label="IP: ", value="192.168.1.23"
      -> "IP:         192.168.1.23"
    """
    label = str(label)
    value = str(value)
    total_len = len(label) + len(value)
    if total_len >= BODY_COLS:
        # No room for padding – just concat
        return label + value
    spaces = BODY_COLS - total_len
    return label + (" " * spaces) + value

def draw_label_value(draw, y, label: str, value: str, *, font=FONT):
    label = str(label)
    value = str(value)

    # left label
    draw.text((0, y), label, font=font, fill=255)

    # right value
    vw = text_width(font, value)
    x = max(0, SCREEN_W - vw)
    draw.text((x, y), value, font=font, fill=255)

def fmt_pair_width(label: str, value: str, width: int) -> str:
    """
    One label/value pair within `width` chars:
      label left, value right.
    If it doesn't fit, it truncates the value (keeping the rightmost part).
    """
    label = str(label)
    value = str(value)
    width = max(1, int(width))

    # If label itself is too long, just hard-truncate it.
    if len(label) >= width:
        return label[:width]

    avail_for_value = width - len(label)

    # Keep the rightmost part of value if it overflows.
    if len(value) > avail_for_value:
        value = value[-avail_for_value:]

    spaces = avail_for_value - len(value)
    return label + (" " * spaces) + value

def fmt_two_cols(
    l_label: str, l_value: str,
    r_label: str, r_value: str,
    *,
    total_cols: int = BODY_COLS,
    gap: int = 1,
) -> str:
    total_cols = max(1, int(total_cols))
    gap = max(1, int(gap))

    avail = max(1, total_cols - gap)
    left_w = avail // 2
    right_w = avail - left_w

    left = fmt_pair_width(l_label, l_value, left_w)
    right = fmt_pair_width(r_label, r_value, right_w)

    return left + (" " * gap) + right

def get_ip_address() -> str:
    """Best-effort primary IPv4 address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "unknown"


def get_power_throttled() -> bool:
    """Return True if vcgencmd reports any throttling/undervoltage."""
    try:
        out = subprocess.check_output(
            ["vcgencmd", "get_throttled"]
        ).decode().strip()
        # 'throttled=0x50005'
        _, hexval = out.split("=")
        val = int(hexval, 16)
        return val != 0
    except Exception:
        return False


def fetch_glances(endpoint: str):
    """GET helper with a small timeout for Glances API."""
    try:
        r = requests.get(f"{GLANCES_URL}/{endpoint}", timeout=2)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

def get_mdraid_status(md_name=MD_NAME):
    """
    Returns:
      state: "clean" | "degraded" | "resync" | "check" | "recover" | "unknown"
      info: dict with optional keys:
            {
              "progress": "52.2",
              "finish": "396.1",
              "speed": "99181"
            }
    """
    state = "unknown"
    info = {}

    # 1. Basic state
    try:
        with open(f"/sys/block/{md_name}/md/array_state") as f:
            state_raw = f.read().strip()
    except FileNotFoundError:
        state_raw = None

    # 2. Sync/check action
    try:
        with open(f"/sys/block/{md_name}/md/sync_action") as f:
            sync_action = f.read().strip()
    except FileNotFoundError:
        sync_action = None

    # 3. Parse /proc/mdstat if array is busy
    if sync_action and sync_action not in ("idle", "frozen"):
        try:
            with open("/proc/mdstat") as f:
                mdstat = f.read()

            # Progress percent (resync = 52.2%)
            m_pct = re.search(
                rf"{md_name} :.*?(resync|check|recover)\s*=\s*([\d\.]+)%",
                mdstat, re.DOTALL
            )
            if m_pct:
                info["progress"] = float(m_pct.group(2))

            # Finish time (finish=396.1min)
            m_finish = re.search(r"finish=([\d\.]+)min", mdstat)
            if m_finish:
                info["finish_min"] = float(m_finish.group(1))

            # Speed (speed=99181K/sec)
            m_speed = re.search(r"speed=([\d\.]+)K/sec", mdstat)
            if m_speed:
                info["speed_kps"] = float(m_speed.group(1))

        except Exception:
            pass

    # 4. Normalize state
    if sync_action and sync_action not in ("idle", "frozen"):
        if sync_action in ("resync", "recovery", "recover"):
            state = "resync"
        elif sync_action in ("check", "repair"):
            state = "check"
        else:
            state = sync_action
    elif state_raw:
        if state_raw in ("clean", "active"):
            state = "clean"
        elif "degraded" in state_raw.lower():
            state = "degraded"
        else:
            state = state_raw

    return state, info

def _extract_dev_from_device_name(device_name: str) -> str | None:
    """
    "sda WDC WD80..." -> "sda"
    """
    if not device_name:
        return None
    # safest: first token before whitespace
    dev = device_name.strip().split()[0]
    # sanity check
    if re.fullmatch(r"sd[a-z]+|nvme\d+n\d+|hd[a-z]+", dev):
        return dev
    # fallback: try to find a linux-ish device token anywhere
    m = re.search(r"\b(sd[a-z]+|nvme\d+n\d+|hd[a-z]+)\b", device_name)
    return m.group(1) if m else None


def _extract_temp_from_smart_obj(obj: dict) -> float | None:
    """
    Looks for Temperature_Celsius (usually attr 194) and returns its raw value as float.
    Handles a few variants across drives.
    """
    # Common: attribute 194
    for key in ("194", "190"):  # 190 sometimes used as airflow temp
        a = obj.get(key)
        if isinstance(a, dict):
            name = (a.get("name") or "").lower()
            if "temp" in name or "temperature" in name:
                raw = a.get("raw")
                if raw is None:
                    continue
                # raw may be "49" or "49 (Min/Max ...)" on some outputs; grab first number
                m = re.search(r"(-?\d+(\.\d+)?)", str(raw))
                if m:
                    return float(m.group(1))

    # Fallback: search all attributes for something temperature-like
    for v in obj.values():
        if not isinstance(v, dict):
            continue
        name = (v.get("name") or "").lower()
        if "temperature" in name and "celsius" in name:
            raw = v.get("raw")
            m = re.search(r"(-?\d+(\.\d+)?)", str(raw))
            if m:
                return float(m.group(1))

    return None

def get_uptime_seconds():
    try:
        with open("/proc/uptime") as f:
            return float(f.read().split()[0])
    except Exception:
        return None

def gather_data():
    """Pull all needed data from Glances and system helpers into a dict."""
    data = {
        "ip": get_ip_address(),
        "power_throttled": get_power_throttled(),
    }

    cpu = fetch_glances("cpu")
    load = fetch_glances("load")
    mem = fetch_glances("mem")
    fs = fetch_glances("fs")
    net = fetch_glances("network")
    raid = fetch_glances("raid")
    diskio = fetch_glances("diskio")
    smart = fetch_glances("smart")
    sensors = fetch_glances("sensors")

    data["uptime_s"] = get_uptime_seconds()

    # CPU %
    data["cpu_percent"] = (cpu or {}).get("total", 0.0)

    # Load (1 min)
    data["load1"] = (load or {}).get("min1", 0.0)

    # Memory (bytes -> GB)
    mem_used = (mem or {}).get("used", 0)
    mem_pct = (mem or {}).get("percent", 0.0)
    mem_total = (mem or {}).get("total", 1)
    data["mem_used_gb"] = mem_used / (1024**3)
    data["mem_used_percent"] = mem_pct
    data["mem_total_gb"] = mem_total / (1024**3)

    # Filesystem: /mnt/storage
    fs_used = fs_size = fs_free = fs_percent = None

    if isinstance(fs, list):
        for f in fs:
            if f.get("mnt_point") == "/mnt/storage":
                fs_size = f.get("size")
                fs_used = f.get("used")
                fs_free = f.get("free")
                fs_percent = f.get("percent")
                break

    data["fs_size_b"] = fs_size
    data["fs_used_b"] = fs_used
    data["fs_free_b"] = fs_free
    data["fs_percent"] = fs_percent

    # Network: eth0 in kbps (kilobits per second)
    tx_kbps = rx_kbps = 0.0
    if isinstance(net, list):
        eth0 = next((n for n in net if n.get("interface_name") == "eth0"), None)
        if eth0:
            tx_kbps = eth0.get("bytes_sent_rate_per_sec", 0) / 1024
            rx_kbps = eth0.get("bytes_recv_rate_per_sec", 0) / 1024
    data["net_tx_kbps"] = tx_kbps
    data["net_rx_kbps"] = rx_kbps

    # RAID state
    data["raid_state"], data["raid_info"] = get_mdraid_status(MD_NAME)
    raid = fetch_glances("raid")
    md0 = (raid or {}).get(MD_NAME)
    if isinstance(md0, dict):
        data["raid"] = {
            "status": md0.get("status"),
            "type": md0.get("type"),
            "config": md0.get("config"),
            "used": int(md0["used"]) if str(md0.get("used", "")).isdigit() else None,
            "available": int(md0["available"]) if str(md0.get("available", "")).isdigit() else None,
            "members": sorted((md0.get("components") or {}).keys()),
        }
    else:
        data["raid"] = None

    # Disk IO rates
    data["diskio_rates"] = {}
    if isinstance(diskio, list):
        for d in diskio:
            name = d.get("disk_name")
            if not name:
                continue
            read_kps = d.get("read_bytes_rate_per_sec", 0) / (1024)
            write_kps = d.get("write_bytes_rate_per_sec", 0) / (1024)
            data["diskio_rates"][name] = (read_kps, write_kps)

    # CPU temp from sensors or vcgencmd
    cpu_temp = None
    if isinstance(sensors, list):
        for s in sensors:
            label = (s.get("label") or "").lower()
            if "cpu" in label or "core" in label:
                cpu_temp = s.get("value")
                if cpu_temp is not None:
                    break
    if cpu_temp is None:
        try:
            out = subprocess.check_output(
                ["vcgencmd", "measure_temp"]
            ).decode().strip()
            # 'temp=47.8\'C'
            cpu_temp = float(out.split("=")[1].split("'")[0])
        except Exception:
            cpu_temp = None
    data["cpu_temp"] = cpu_temp

    # Disk temps from SMART (Glances /smart endpoint returns a list of dicts)
    disk_temps = {}
    if isinstance(smart, list):
        for obj in smart:
            if not isinstance(obj, dict):
                continue
            dev = _extract_dev_from_device_name(obj.get("DeviceName", ""))
            if not dev:
                continue
            temp = _extract_temp_from_smart_obj(obj)
            if temp is not None:
                disk_temps[dev] = temp
    data["disk_temps"] = disk_temps

    return data

def draw_raid_ok(draw, x, y):
    for dx, dy in CLEAN_FRAME:
        draw.point((x + dx, y + dy), fill=255)

def draw_clean_big(draw, x, y):
    for dx, dy in CLEAN_FRAME:
        px = x + dx * 2
        py = y + dy * 2
        draw.rectangle((px, py, px + 1, py + 1), outline=255, fill=255)

def draw_raid_sync(draw, x, y):
    coords = REBUILD_FRAMES[SPIN_FRAME]
    for dx, dy in coords:
        draw.point((x + dx, y + dy), fill=255)

def draw_resync_big(draw, x, y):
    frame = REBUILD_FRAMES[SPIN_FRAME]
    for dx, dy in frame:
        px = x + dx * 2
        py = y + dy * 2
        # 2x2 block for each lit pixel
        draw.rectangle((px, py, px + 1, py + 1), outline=255, fill=255)


def draw_raid_degraded(draw, x, y):
    idx = (SPIN_FRAME // 2) % 2
    for dx, dy in DEGRADED_FRAMES[idx]:
        draw.point((x + dx, y + dy), fill=255)


def draw_raid_unknown(draw, x, y):
    idx = (SPIN_FRAME // 2) % 2
    for dx, dy in UNKNOWN_FRAMES[idx]:
        draw.point((x + dx, y + dy), fill=255)


def draw_power_icon(draw, x, y, throttled: bool):
    if not throttled:
        return
    idx = (SPIN_FRAME // 2) % 2
    for dx, dy in POWER_FRAMES[idx]:
        draw.point((x + dx, y + dy), fill=255)


def draw_header(draw, device, title, data):
    draw.text((HEADER_TEXT_X, HEADER_TEXT_Y), title, font=HEADER_FONT, fill=255)
    draw_power_icon(draw, HEADER_ICON_X, HEADER_ICON_Y, data.get("power_throttled", False))

def fmt_rw_mb(r: float, w: float) -> str:
    """
    Format read/write MB/s as fixed-width string within limited chars.
    Example: "R0.0 W1.2"
    """
    return f"R{r:3.1f} W{w:3.1f}"

def draw_progress_bar_line(draw, line_y, pct):
    """
    Draw a progress bar visually aligned to a text line.
    - 1px top margin
    - slightly more breathing room on the bottom
    """
    x = 0
    y = line_y + 1           # top margin stays correct
    w = SCREEN_W
    h = LINE_HEIGHT - 3      # 1px shorter than before

    # Outline
    draw.rectangle(
        (x, y, x + w - 1, y + h - 1),
        outline=255,
        fill=0
    )

    # Parse percent
    try:
        p = float(pct)
    except (TypeError, ValueError):
        return

    p = max(0.0, min(100.0, p))

    # Fill
    inner_w = max(0, w - 2)
    fill_w = int((p / 100.0) * inner_w)

    if fill_w > 0:
        draw.rectangle(
            (x + 1, y + 1, x + fill_w, y + h - 2),
            outline=255,
            fill=255
        )

def next_col_x(px: int, *, font=FONT) -> int:
    """
    Snap `px` to the next text column boundary (monospace-ish).
    Uses the width of a single '0' cell in your current font.
    """
    cw = max(1, text_width(font, "0"))
    return int(math.ceil(px / cw) * cw)

def draw_body_line(draw, line_y, label: str, value: str, *, font=FONT):
    """
    Draw one standard body line using your fixed-width formatter.
    (No pixel measurement; uses BODY_COLS.)
    """
    draw.text(
        (0, line_y),
        fmt_label_value(label, value),
        font=font,
        fill=255,
    )

def draw_body_text(draw, line_y, text: str, *, font=FONT):
    """
    Draw one standard body line where you already formatted the whole string
    (ex: fmt_two_cols output).
    """
    draw.text((0, line_y), str(text), font=font, fill=255)

def draw_body_lines(draw, lines, *, font=FONT):
    """
    Convenience for pages that just want to emit 1–3 label/value lines.
    Example:
      draw_body_lines(draw, [
        (BODY_TEXT_LINE_1, "CPU:", cpu_val),
        (BODY_TEXT_LINE_2, "Mem:", mem_val),
        (BODY_TEXT_LINE_3, "Temp:", temp_val),
      ])
    """
    for item in lines:
        if not item:
            continue
        y, label, value = item
        draw_body_line(draw, y, label, value, font=font)

def draw_body_line_at(draw, x, line_y, label: str, value: str, *, font=FONT):
    """
    Like draw_body_line, but label starts at `x` (pixels).
    Value is still right-aligned to SCREEN_W.
    """
    label = str(label)
    value = str(value)

    draw.text((x, line_y), label, font=font, fill=255)

    vw = text_width(font, value)
    vx = max(0, SCREEN_W - vw)
    draw.text((vx, line_y), value, font=font, fill=255)

def draw_body_lines_at(draw, x, lines, *, font=FONT):
    """
    Batch version for indented label/value lines.
    lines items are (y, label, value).
    """
    for item in lines:
        if not item:
            continue
        y, label, value = item
        draw_body_line_at(draw, x, y, label, value, font=font)

# -------------------------
# Page renderers
# -------------------------

def page_network(draw, device, data):
    draw_header(draw, device, "Network", data)

    ip = data.get("ip", "unknown")
    tx = fmt_rate(data.get("net_tx_kbps", 0.0))
    rx = fmt_rate(data.get("net_rx_kbps", 0.0))
    rate = fmt_two_cols("▲", tx, "▼", rx)

    uptime_val = fmt_time(data.get("uptime_s"))

    draw_body_line(draw, L1, "IP:", ip)
    draw_body_text(draw, L2, rate)
    draw_body_line(draw, L3, "Uptime:", uptime_val)

def page_system(draw, device, data):
    draw_header(draw, device, "System", data)

    cpu = data.get("cpu_percent", 0.0)
    load = data.get("load1", 0.0)
    cpu_val = "N/A" if cpu is None else f"{cpu:3.0f}% ({load:0.2f})"

    mem = data.get("mem_used_percent", 0.0)
    mem_total = data.get("mem_total_gb", 1.0)
    mem_val = "N/A" if mem is None else f"{mem:3.0f}% of {mem_total:0.1f}G"

    temp_val = fmt_temp(data.get("cpu_temp"))

    draw_body_lines(draw, [
        (L1, "CPU:",  cpu_val),
        (L2, "Mem:",  mem_val),
        (L3, "Temp:", temp_val),
    ])

def page_storage(draw, device, data):
    draw_header(draw, device, "Storage", data)

    used_val = fmt_bytes(data.get("fs_used_b"))
    free_val = fmt_bytes(data.get("fs_free_b"))

    draw_body_lines(draw, [
        (L1, "Used:", used_val),
        (L2, "Free:", free_val),
    ])
    draw_progress_bar_line(draw, L3, data.get("fs_percent"))

def page_raid(draw, device, data):
    draw_header(draw, device, "RAID", data)

    r = data.get("raid") or {}

    status = (r.get("status") or "N/A").lower()
    rtype  = (r.get("type") or "N/A").lower()
    config = (r.get("config") or "N/A")

    used = r.get("used")
    avail = r.get("available")

    state_val = f"{status} ({rtype})" if rtype != "n/a" else status

    if isinstance(used, int) and isinstance(avail, int):
        health_val = f"{used}/{avail} {config}"
    else:
        health_val = config

    # A simple degraded indicator from config: any '_' means missing member(s)
    if "_" in config:
        health_val = f"DEGRADED {health_val}"

    members = r.get("members") or []
    members_val = " ".join(members) if members else "N/A"

    draw_body_lines(draw, [
        (L1, "State:",  state_val),
        (L2, "Health:",  health_val),
        (L3, "Disks:", members_val),
    ])

def page_temps(draw, device, data):
    draw_header(draw, device, "Temps", data)

    disk_temps = data.get("disk_temps", {})

    draw_body_lines(draw, [
        (L1, "CPU:",  fmt_temp(data.get("cpu_temp"))),
        (L2, "sda:",  fmt_temp(disk_temps.get("sda"))),
        (L3, "sdb:", fmt_temp(disk_temps.get("sdb"))),
    ])
    
def page_resync(draw, device, data):
    draw_header(draw, device, "Resyncing...", data)
    draw_resync_big(draw, 0, BODY_ICON_Y)

    # Raid Info
    info = data.get("raid_info", {})
    prog_val = "N/A" if info.get('progress') is None else f"{info.get('progress', 0.0):.1f}%"
    rate_val = "N/A" if info.get('speed_kps') is None else fmt_rate(info.get('speed_kps', 0.0))
    eta_val = "N/A" if info.get('finish_min') is None else fmt_minutes(info.get('finish_min', 0.0))

    draw_body_lines_at(draw, 34, [
        (L1, "Prog:", prog_val),
        (L2, "Rate:", rate_val),
        (L3, "ETA:", eta_val),
    ])

def page_clean(draw, device, data):
    draw_header(draw, device, "Online", data)
    draw_clean_big(draw, 0, BODY_ICON_Y)

    # Used
    fs_used = data.get("fs_percent")
    used_val = "N/A" if fs_used is None else f"{fs_used:.1f}%"
    
    # R/W
    diskio = data.get("diskio_rates", {})
    rw_val = fmt_rate(sum(diskio.get(MD_NAME, (0.0, 0.0))))
    
    # Temp
    disk_temps = data.get("disk_temps", {})
    temp = max(disk_temps.values(), default=None)
    temp_val = "N/A" if temp is None else fmt_temp(temp)

    draw_body_lines_at(draw, 34, [
        (L1, "Used:", used_val),
        (L2, "R/W:",  rw_val),
        (L3, "Temp:", temp_val),
    ])

def draw_loading_screen(device, text="Loading…"):
    image = Image.new("1", (device.width, device.height))
    draw = ImageDraw.Draw(image)

    try:
        w = int(FONT.getlength(text))
        h = LINE_HEIGHT
    except Exception:
        bbox = draw.textbbox((0, 0), text, font=FONT)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
    
    x = (SCREEN_W - w) // 2
    y = BODY_CENTER_Y - (LINE_HEIGHT // 2)

    draw.text((x, y), text, font=FONT, fill=255)
    device.display(image)

def draw_fatal_error(device, line1, line2=None):
    image = Image.new("1", (device.width, device.height))
    draw = ImageDraw.Draw(image)

    draw.text((0, BODY_TEXT_LINE_2), line1, font=FONT, fill=255)
    if line2:
        draw.text((0, BODY_TEXT_LINE_3), line2, font=FONT, fill=255)

    device.display(image)

# -------------------------
# Main loop
# -------------------------

current_page = -1     # -1 means "home mode"
last_nav_at = 0.0     # monotonic timestamp of last user navigation

def _on_button(channel):
    global current_page, last_nav_at

    now = time.monotonic()
    last_nav_at = now

    # if we were in home mode, start at first browse page
    if current_page == -1:
        current_page = 0
    else:
        current_page = (current_page + 1) % len(PAGE_FUNCS)

def gpio_init():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(
        BUTTON_PIN,
        GPIO.FALLING,
        callback=_on_button,
        bouncetime=250
    )

PAGE_FUNCS = [page_network, page_system, page_storage, page_raid, page_temps]

def render_home(draw, device, data):
    raid_state = (data.get("raid_state") or "").lower()
    if raid_state == "resync":
        page_resync(draw, device, data)
    else:
        page_clean(draw, device, data)

def clear_display(device):
    image = Image.new("1", (device.width, device.height))
    device.display(image)

def main():
    global LAST_DATA, LAST_DATA_TS, SPIN_FRAME, current_page, last_nav_at, MD_NAME

    serial = i2c(port=1, address=I2C_ADDRESS)
    device = ssd1306(serial, width=128, height=64)

    draw_loading_screen(device, "Loading...")

    def handle_shutdown(signum, frame):
        clear_display(device)
        GPIO.cleanup()
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    MD_NAME = resolve_md_name("/mnt/storage")
    if not MD_NAME:
        draw_fatal_error(device, "RAID not found", "/mnt/storage")
        time.sleep(5)
        clear_display(device)
        return

    gpio_init()

    LAST_DATA = gather_data()
    LAST_DATA_TS = time.time()

    while True:
        now_wall = time.time()
        now_mono = time.monotonic()

        # Refresh data every DATA_INTERVAL
        if now_wall - LAST_DATA_TS >= DATA_INTERVAL:
            LAST_DATA = gather_data()
            LAST_DATA_TS = now_wall

        # Auto-return to home if user hasn't navigated recently
        if current_page != -1 and (now_mono - last_nav_at) >= NAV_TIMEOUT:
            current_page = -1

        # Advance animation frame
        SPIN_FRAME = (SPIN_FRAME + 1) % 4

        # Render
        image = Image.new("1", (device.width, device.height))
        draw = ImageDraw.Draw(image)

        # Copy locals to avoid race conditions (thread-safety)
        page = current_page
        nav_at = last_nav_at

        try:
            if DEBUG_PAGE is not None:
                DEBUG_PAGE(draw, device, LAST_DATA)
            elif page == -1 and (now_mono - nav_at) >= NAV_TIMEOUT:
                render_home(draw, device, LAST_DATA)
            else:
                PAGE_FUNCS[page](draw, device, LAST_DATA)
        except Exception as e:
            draw.text((0, 0), "OLED ERR", font=FONT, fill=255)
            draw.text((0, 16), str(e), font=FONT, fill=255)

        device.display(image)
        time.sleep(DISPLAY_INTERVAL)

DEBUG_PAGE = None
# DEBUG_PAGE = page_resync
# DEBUG_PAGE = page_clean
# DEBUG_PAGE = page_network
# DEBUG_PAGE = page_system
# DEBUG_PAGE = page_storage
# DEBUG_PAGE = page_raid
# DEBUG_PAGE = page_temps


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        try:
            clear_display(device)
        except Exception:
            pass
        GPIO.cleanup()
