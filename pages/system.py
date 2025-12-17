"""System page."""

from hardware.display import draw_header, draw_body_lines, fmt_temp
from config import L1, L2, L3


def render(draw, ctx):
    """Render system page."""
    draw_header(draw, ctx, "System")

    # CPU usage and load
    cpu_data = ctx.glances.get("cpu", ttl_s=2.0) or {}
    cpu = cpu_data.get("total", 0.0)

    load_data = ctx.glances.get("load", ttl_s=2.0) or {}
    load = load_data.get("min1", 0.0)

    cpu_val = f"{cpu:3.0f}% ({load:0.2f})"

    # Memory
    mem_data = ctx.glances.get("mem", ttl_s=2.0) or {}
    mem_pct = mem_data.get("percent", 0.0)
    mem_total = mem_data.get("total", 1) / (1024**3)
    mem_val = f"{mem_pct:3.0f}% of {mem_total:0.1f}G"

    # CPU temperature
    sensors = ctx.glances.get("sensors", ttl_s=5.0) or []
    temp_val_raw = None
    for s in sensors:
        label = (s.get("label") or "").lower()
        if "cpu" in label or "core" in label:
            temp_val_raw = s.get("value")
            break

    # Fallback to vcgencmd
    if temp_val_raw is None:
        temp_val_raw = ctx.system.get("cpu_temp", ttl_s=5.0)

    temp_val = fmt_temp(temp_val_raw)

    draw_body_lines(draw, [
        (L1, "CPU:", cpu_val),
        (L2, "Mem:", mem_val),
        (L3, "Temp:", temp_val),
    ])
