"""Temperatures page."""

from render import draw_header, draw_body_lines, fmt_temp
from config import L1, L2, L3


def render(draw, ctx):
    """Render temperatures page."""
    draw_header(draw, ctx, "Temps")

    # CPU temp from sensors
    sensors = ctx.glances.get("sensors", ttl_s=5.0) or []
    cpu_temp = None
    for s in sensors:
        label = (s.get("label") or "").lower()
        if "cpu" in label or "core" in label:
            cpu_temp = s.get("value")
            break

    # Fallback to vcgencmd
    if cpu_temp is None:
        cpu_temp = ctx.system.get("cpu_temp", ttl_s=5.0)

    # Disk temps
    smart = ctx.glances.get("smart", ttl_s=10.0) or {}

    draw_body_lines(draw, [
        (L1, "CPU:", fmt_temp(cpu_temp)),
        (L2, "sda:", fmt_temp(smart.get("sda", {}).get("temperature_c"))),
        (L3, "sdb:", fmt_temp(smart.get("sdb", {}).get("temperature_c"))),
    ])
