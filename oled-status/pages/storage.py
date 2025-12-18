"""Storage page."""

from hardware.display import draw_header, draw_body_lines, draw_progress_bar_line, fmt_bytes
from config import L1, L2, L3


def render(draw, ctx):
    """Render storage page."""
    draw_header(draw, ctx, "Storage")

    fs_list = ctx.glances.get("fs", ttl_s=5.0) or []

    fs_used = fs_free = fs_percent = None
    for f in fs_list:
        if f.get("mnt_point") == "/mnt/storage":
            fs_used = f.get("used")
            fs_free = f.get("free")
            fs_percent = f.get("percent")
            break

    used_val = fmt_bytes(fs_used)
    free_val = fmt_bytes(fs_free)

    draw_body_lines(draw, [
        (L1, "Used:", used_val),
        (L2, "Free:", free_val),
    ])
    draw_progress_bar_line(draw, L3, fs_percent)
