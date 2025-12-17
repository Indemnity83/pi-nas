"""RAID page."""

from render import draw_header, draw_body_lines
from config import L1, L2, L3


def render(draw, ctx):
    """Render RAID page."""
    draw_header(draw, ctx, "RAID")

    raid_list = ctx.glances.get("raid", ttl_s=5.0) or {}
    md_name = ctx.mdadm.get("name")

    r = raid_list.get(md_name, {})

    status = (r.get("status") or "N/A").lower()
    rtype = (r.get("type") or "N/A").lower()
    config = (r.get("config") or "N/A")

    used = r.get("used")
    avail = r.get("available")

    state_val = f"{status} ({rtype})" if rtype != "n/a" else status

    if isinstance(used, int) and isinstance(avail, int):
        health_val = f"{used}/{avail} {config}"
    else:
        health_val = config

    # Degraded indicator from config
    if "_" in config:
        health_val = f"DEGRADED {health_val}"

    members = r.get("members") or []
    members_val = " ".join(members) if members else "N/A"

    draw_body_lines(draw, [
        (L1, "State:", state_val),
        (L2, "Health:", health_val),
        (L3, "Disks:", members_val),
    ])
