"""Rendering utilities, formatters, and icon definitions."""

import math
from PIL import ImageFont
from config import SCREEN_W, SCREEN_H, HEADER_HEIGHT, LINE_HEIGHT
from config import HEADER_TEXT_X, HEADER_TEXT_Y, HEADER_ICON_X, HEADER_ICON_Y

# Fonts
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

# Font metrics
def text_width(font, s: str) -> int:
    """Calculate pixel width of text."""
    try:
        return math.ceil(font.getlength(s))
    except AttributeError:
        bbox = font.getbbox(s)
        return bbox[2] - bbox[0]

def compute_cols_fit(screen_w: int, font, sample_char: str = "0") -> int:
    """Find max N such that N sample chars fit in screen_w."""
    lo, hi = 1, 64
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if text_width(font, sample_char * mid) <= screen_w:
            lo = mid
        else:
            hi = mid - 1
    return lo

BODY_COLS = compute_cols_fit(SCREEN_W, FONT)
HEADER_COLS = compute_cols_fit(SCREEN_W, HEADER_FONT)

# Animation frame counter (used externally)
_SPIN_FRAME = 0

def get_spin_frame():
    """Get current animation frame."""
    return _SPIN_FRAME

def advance_spin_frame():
    """Advance animation frame."""
    global _SPIN_FRAME
    _SPIN_FRAME = (_SPIN_FRAME + 1) % 4

# Icon creation helper
def make_icon(pattern):
    """Convert a 14x14 pattern of '.' and '#' into (x, y) coords."""
    coords = []
    for y, row in enumerate(pattern):
        for x, ch in enumerate(row):
            if ch == '#':
                coords.append((x, y))
    return coords

# Icon patterns
REBUILD_PATTERNS = [
    [
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
    [
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
    [
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
    [
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

DEGRADED_PATTERNS = [
    [
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
    [
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

UNKNOWN_PATTERNS = [
    [
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
    [
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

POWER_PATTERNS = [
    [
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
    [
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
]

REBUILD_FRAMES = [make_icon(p) for p in REBUILD_PATTERNS]
DEGRADED_FRAMES = [make_icon(p) for p in DEGRADED_PATTERNS]
UNKNOWN_FRAMES = [make_icon(p) for p in UNKNOWN_PATTERNS]
CLEAN_FRAME = make_icon(CLEAN_PATTERN)
POWER_FRAMES = [make_icon(p) for p in POWER_PATTERNS]

# Formatters
def fmt_rate(k_per_s):
    """Convert K/s to human readable rate."""
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
    """Format minutes as human readable time."""
    return fmt_time(minutes * 60)

def fmt_time(seconds):
    """Format seconds as human readable time."""
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
    """Format bytes as human readable size."""
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

    return f"{n:.0f}{units[i]}" if i < 2 else f"{n:.1f}{units[i]}"

def fmt_temp(val, *, warn=50.0, hot=60.0) -> str:
    """Format temperature with visual severity markers."""
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
    """Return string with label left-aligned and value right-aligned."""
    label = str(label)
    value = str(value)
    total_len = len(label) + len(value)
    if total_len >= BODY_COLS:
        return label + value
    spaces = BODY_COLS - total_len
    return label + (" " * spaces) + value

def fmt_pair_width(label: str, value: str, width: int) -> str:
    """Format label/value pair within width chars."""
    label = str(label)
    value = str(value)
    width = max(1, int(width))

    if len(label) >= width:
        return label[:width]

    avail_for_value = width - len(label)

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
    """Format two label/value pairs side by side."""
    total_cols = max(1, int(total_cols))
    gap = max(1, int(gap))

    avail = max(1, total_cols - gap)
    left_w = avail // 2
    right_w = avail - left_w

    left = fmt_pair_width(l_label, l_value, left_w)
    right = fmt_pair_width(r_label, r_value, right_w)

    return left + (" " * gap) + right

# Drawing helpers
def draw_label_value(draw, y, label: str, value: str, *, font=FONT):
    """Draw label on left, value on right."""
    label = str(label)
    value = str(value)

    draw.text((0, y), label, font=font, fill=255)

    vw = text_width(font, value)
    x = max(0, SCREEN_W - vw)
    draw.text((x, y), value, font=font, fill=255)

def next_col_x(px: int, *, font=FONT) -> int:
    """Snap px to next text column boundary."""
    cw = max(1, text_width(font, "0"))
    return int(math.ceil(px / cw) * cw)

def draw_body_line(draw, line_y, label: str, value: str, *, font=FONT):
    """Draw one standard body line."""
    draw.text(
        (0, line_y),
        fmt_label_value(label, value),
        font=font,
        fill=255,
    )

def draw_body_text(draw, line_y, text: str, *, font=FONT):
    """Draw one standard body line with pre-formatted text."""
    draw.text((0, line_y), str(text), font=font, fill=255)

def draw_body_lines(draw, lines, *, font=FONT):
    """Draw multiple body lines from list of (y, label, value) tuples."""
    for item in lines:
        if not item:
            continue
        y, label, value = item
        draw_body_line(draw, y, label, value, font=font)

def draw_body_line_at(draw, x, line_y, label: str, value: str, *, font=FONT):
    """Draw label/value line with label starting at x."""
    label = str(label)
    value = str(value)

    draw.text((x, line_y), label, font=font, fill=255)

    vw = text_width(font, value)
    vx = max(0, SCREEN_W - vw)
    draw.text((vx, line_y), value, font=font, fill=255)

def draw_body_lines_at(draw, x, lines, *, font=FONT):
    """Draw multiple body lines with indent."""
    for item in lines:
        if not item:
            continue
        y, label, value = item
        draw_body_line_at(draw, x, y, label, value, font=font)

def draw_progress_bar_line(draw, line_y, pct):
    """Draw a progress bar at the given line."""
    x = 0
    y = line_y + 1
    w = SCREEN_W
    h = LINE_HEIGHT - 3

    # Outline
    draw.rectangle((x, y, x + w - 1, y + h - 1), outline=255, fill=0)

    try:
        p = float(pct)
    except (TypeError, ValueError):
        return

    p = max(0.0, min(100.0, p))

    # Fill
    inner_w = max(0, w - 2)
    fill_w = int((p / 100.0) * inner_w)

    if fill_w > 0:
        draw.rectangle((x + 1, y + 1, x + fill_w, y + h - 2), outline=255, fill=255)

# Icon drawing
def draw_raid_ok(draw, x, y):
    """Draw clean RAID icon."""
    for dx, dy in CLEAN_FRAME:
        draw.point((x + dx, y + dy), fill=255)

def draw_clean_big(draw, x, y):
    """Draw large clean RAID icon."""
    for dx, dy in CLEAN_FRAME:
        px = x + dx * 2
        py = y + dy * 2
        draw.rectangle((px, py, px + 1, py + 1), outline=255, fill=255)

def draw_raid_sync(draw, x, y):
    """Draw animated rebuild icon."""
    coords = REBUILD_FRAMES[_SPIN_FRAME]
    for dx, dy in coords:
        draw.point((x + dx, y + dy), fill=255)

def draw_resync_big(draw, x, y):
    """Draw large animated rebuild icon."""
    frame = REBUILD_FRAMES[_SPIN_FRAME]
    for dx, dy in frame:
        px = x + dx * 2
        py = y + dy * 2
        draw.rectangle((px, py, px + 1, py + 1), outline=255, fill=255)

def draw_raid_degraded(draw, x, y):
    """Draw animated degraded icon."""
    idx = (_SPIN_FRAME // 2) % 2
    for dx, dy in DEGRADED_FRAMES[idx]:
        draw.point((x + dx, y + dy), fill=255)

def draw_raid_unknown(draw, x, y):
    """Draw animated unknown icon."""
    idx = (_SPIN_FRAME // 2) % 2
    for dx, dy in UNKNOWN_FRAMES[idx]:
        draw.point((x + dx, y + dy), fill=255)

def draw_power_icon(draw, x, y, throttled: bool):
    """Draw power warning icon if throttled."""
    if not throttled:
        return
    idx = (_SPIN_FRAME // 2) % 2
    for dx, dy in POWER_FRAMES[idx]:
        draw.point((x + dx, y + dy), fill=255)

def draw_header(draw, ctx, title):
    """Draw standard page header with throttle status."""
    draw.text((HEADER_TEXT_X, HEADER_TEXT_Y), title, font=HEADER_FONT, fill=255)

    # Check throttle status
    throttle = ctx.system.get("power_throttled", ttl_s=5.0)
    is_throttled = any([throttle.get("under_voltage"), throttle.get("throttled")])

    draw_power_icon(draw, HEADER_ICON_X, HEADER_ICON_Y, is_throttled)
