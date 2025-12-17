"""Display rendering utilities, formatters, and icon definitions."""

import math
from PIL import Image, ImageDraw, ImageFont
from config import SCREEN_W, SCREEN_H, HEADER_HEIGHT, LINE_HEIGHT
from config import HEADER_TEXT_X, HEADER_TEXT_Y, HEADER_ICON_X, HEADER_ICON_Y
from config import BODY_CENTER_Y, L2, L3

# Import formatters (pure Python, no dependencies)
from formatters import (
    fmt_rate, fmt_minutes, fmt_time, fmt_bytes, fmt_temp,
    fmt_label_value, fmt_pair_width, fmt_two_cols
)


class Display:
    """OLED display hardware control."""

    # Class-level animation state
    _frame = 0

    def __init__(self, device):
        """
        Initialize Display instance.

        Args:
            device: Initialized luma device (ssd1306)
        """
        self.device = device

    @classmethod
    def init(cls):
        """
        Initialize OLED display device.

        Returns:
            Display instance with initialized device
        """
        from luma.core.interface.serial import i2c
        from luma.oled.device import ssd1306
        from config import I2C_ADDRESS

        serial = i2c(port=1, address=I2C_ADDRESS)
        device = ssd1306(serial, width=128, height=64)
        return cls(device)

    def draw(self, image):
        """Draw an image to the display."""
        self.device.display(image)

    def render(self, page, ctx):
        """
        Render a page to the display.

        Args:
            page: Function that takes (draw, ctx) and renders to draw
            ctx: Context object to pass to page
        """
        image = Image.new("1", (self.device.width, self.device.height))
        draw = ImageDraw.Draw(image)
        page(draw, ctx)
        self.draw(image)

    def clear(self):
        """Clear the display."""
        image = Image.new("1", (self.device.width, self.device.height))
        self.device.display(image)

    def draw_loading_screen(self, text="Loading…"):
        """Show loading message on display."""
        image = Image.new("1", (self.device.width, self.device.height))
        draw = ImageDraw.Draw(image)

        try:
            w = int(FONT.getlength(text))
        except Exception:
            bbox = draw.textbbox((0, 0), text, font=FONT)
            w = bbox[2] - bbox[0]

        x = (SCREEN_W - w) // 2
        y = BODY_CENTER_Y - (LINE_HEIGHT // 2)

        draw.text((x, y), text, font=FONT, fill=255)
        self.device.display(image)

    def draw_fatal_error(self, line1, line2=None):
        """Show fatal error on display."""
        image = Image.new("1", (self.device.width, self.device.height))
        draw = ImageDraw.Draw(image)

        draw.text((0, L2), line1, font=FONT, fill=255)
        if line2:
            draw.text((0, L3), line2, font=FONT, fill=255)

        self.device.display(image)

    def show_error(self, error_text):
        """Show runtime error on display."""
        image = Image.new("1", (self.device.width, self.device.height))
        draw = ImageDraw.Draw(image)

        draw.text((0, 0), "OLED ERR", font=FONT, fill=255)
        draw.text((0, 16), str(error_text)[:20], font=FONT, fill=255)

        self.device.display(image)

    @classmethod
    def advance_frame(cls):
        """Advance animation frame."""
        cls._frame = (cls._frame + 1) % 4

    @classmethod
    def get_frame(cls):
        """Get current animation frame."""
        return cls._frame

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

# Large triangle warning icon patterns (28x28 for body)
DEGRADED_BIG_PATTERNS = [
    # Frame 1: Triangle with exclamation mark
    [
        ".............##.............",
        "............####............",
        "...........##..##...........",
        "..........##....##..........",
        ".........##......##.........",
        "........##........##........",
        ".......##....##....##.......",
        "......##.....##.....##......",
        ".....##......##......##.....",
        "....##.......##.......##....",
        "...##........##........##...",
        "..##.........##.........##..",
        ".##..........##..........##.",
        "##...........##...........##",
        "##...........##...........##",
        "##...........##...........##",
        "##.......................##",
        "##.......................##",
        "##.......................##",
        "##.......................##",
        "##.......................##",
        "##.......................##",
        "##..........####.........##",
        "##..........####.........##",
        "##.......................##",
        ".##.....................##.",
        "..##...................##..",
        "....################....",
    ],
    # Frame 2: Triangle without exclamation (blink)
    [
        ".............##.............",
        "............####............",
        "...........##..##...........",
        "..........##....##..........",
        ".........##......##.........",
        "........##........##........",
        ".......##..........##.......",
        "......##............##......",
        ".....##..............##.....",
        "....##................##....",
        "...##..................##...",
        "..##....................##..",
        ".##......................##.",
        "##........................##",
        "##........................##",
        "##........................##",
        "##........................##",
        "##........................##",
        "##........................##",
        "##........................##",
        "##........................##",
        "##........................##",
        "##........................##",
        "##........................##",
        "##........................##",
        ".##......................##.",
        "..##....................##..",
        "....################....",
    ],
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
DEGRADED_BIG_FRAMES = [make_icon(p) for p in DEGRADED_BIG_PATTERNS]
UNKNOWN_FRAMES = [make_icon(p) for p in UNKNOWN_PATTERNS]
CLEAN_FRAME = make_icon(CLEAN_PATTERN)
POWER_FRAMES = [make_icon(p) for p in POWER_PATTERNS]

# Note: Formatters now imported from formatters.py module above

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
        fmt_label_value(label, value, BODY_COLS),
        font=font,
        fill=255,
    )

def draw_body_text(draw, line_y, text: str, *, font=FONT):
    """Draw one standard body line with pre-formatted text."""
    draw.text((0, line_y), str(text), font=font, fill=255)

def fmt_two_cols_default(l_label: str, l_value: str, r_label: str, r_value: str, gap: int = 1) -> str:
    """Wrapper for fmt_two_cols with BODY_COLS default."""
    return fmt_two_cols(l_label, l_value, r_label, r_value, total_cols=BODY_COLS, gap=gap)

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

def draw_degraded_big(draw, x, y):
    """Draw large animated degraded warning icon."""
    idx = (Display.get_frame() // 2) % 2
    frame = DEGRADED_BIG_FRAMES[idx]
    for dx, dy in frame:
        draw.point((x + dx, y + dy), fill=255)

def draw_raid_sync(draw, x, y):
    """Draw animated rebuild icon."""
    coords = REBUILD_FRAMES[Display.get_frame()]
    for dx, dy in coords:
        draw.point((x + dx, y + dy), fill=255)

def draw_resync_big(draw, x, y):
    """Draw large animated rebuild icon."""
    frame = REBUILD_FRAMES[Display.get_frame()]
    for dx, dy in frame:
        px = x + dx * 2
        py = y + dy * 2
        draw.rectangle((px, py, px + 1, py + 1), outline=255, fill=255)

def draw_raid_degraded(draw, x, y):
    """Draw animated degraded icon."""
    idx = (Display.get_frame() // 2) % 2
    for dx, dy in DEGRADED_FRAMES[idx]:
        draw.point((x + dx, y + dy), fill=255)

def draw_raid_unknown(draw, x, y):
    """Draw animated unknown icon."""
    idx = (Display.get_frame() // 2) % 2
    for dx, dy in UNKNOWN_FRAMES[idx]:
        draw.point((x + dx, y + dy), fill=255)

def draw_power_icon(draw, x, y, throttled: bool):
    """Draw power warning icon if throttled."""
    if not throttled:
        return
    idx = (Display.get_frame() // 2) % 2
    for dx, dy in POWER_FRAMES[idx]:
        draw.point((x + dx, y + dy), fill=255)

def draw_header(draw, ctx, title):
    """Draw standard page header with throttle status."""
    draw.text((HEADER_TEXT_X, HEADER_TEXT_Y), title, font=HEADER_FONT, fill=255)

    # Check throttle status
    throttle = ctx.system.get("power_throttled", ttl_s=5.0)
    is_throttled = any([throttle.get("under_voltage"), throttle.get("throttled")])

    draw_power_icon(draw, HEADER_ICON_X, HEADER_ICON_Y, is_throttled)
