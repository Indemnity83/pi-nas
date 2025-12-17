"""Home page - shows RAID status overview."""

from render import draw_header, draw_body_lines_at
from render import draw_clean_big, draw_resync_big
from render import fmt_temp, fmt_rate
from config import L1, L2, L3, BODY_ICON_Y


def render(draw, ctx):
    """Render home page based on RAID state."""
    raid_status = ctx.mdadm.get("status", ttl_s=2.0)

    # Interpret raw RAID state
    sync_action = raid_status.get("sync_action", "")
    array_state = raid_status.get("array_state", "")

    # Show resync page if actively resyncing/recovering
    if sync_action and sync_action not in ("idle", "frozen"):
        if sync_action in ("resync", "recovery", "recover", "check", "repair"):
            _render_resync(draw, ctx, raid_status)
            return

    # Otherwise show clean/normal page
    _render_clean(draw, ctx)


def _render_resync(draw, ctx, raid_status):
    """Render resyncing state."""
    draw_header(draw, ctx, "Resyncing...")
    draw_resync_big(draw, 0, BODY_ICON_Y)

    prog_val = "N/A" if raid_status.get('progress') is None else f"{raid_status.get('progress', 0.0):.1f}%"
    rate_val = "N/A" if raid_status.get('speed_kps') is None else fmt_rate(raid_status.get('speed_kps', 0.0))

    finish_min = raid_status.get('finish_min')
    if finish_min is not None:
        eta_s = finish_min * 60
        eta_val = _fmt_time_short(eta_s)
    else:
        eta_val = "N/A"

    draw_body_lines_at(draw, 34, [
        (L1, "Prog:", prog_val),
        (L2, "Rate:", rate_val),
        (L3, "ETA:", eta_val),
    ])


def _render_clean(draw, ctx):
    """Render clean/online state."""
    draw_header(draw, ctx, "Online")
    draw_clean_big(draw, 0, BODY_ICON_Y)

    # Filesystem usage
    fs_list = ctx.glances.get("fs", ttl_s=5.0) or []
    fs_percent = None
    for f in fs_list:
        if f.get("mnt_point") == "/mnt/storage":
            fs_percent = f.get("percent")
            break
    used_val = "N/A" if fs_percent is None else f"{fs_percent:.1f}%"

    # Disk IO
    diskio_list = ctx.glances.get("diskio", ttl_s=2.0) or []
    md_name = ctx.mdadm.get("name")
    rw_kps = 0.0
    for d in diskio_list:
        if d.get("disk_name") == md_name:
            rw_kps = sum([
                d.get("read_bytes_rate_per_sec", 0) / 1024,
                d.get("write_bytes_rate_per_sec", 0) / 1024,
            ])
            break
    rw_val = fmt_rate(rw_kps)

    # Disk temps
    smart = ctx.glances.get("smart", ttl_s=10.0) or {}
    temps = [d.get("temperature_c") for d in smart.values() if d.get("temperature_c") is not None]
    temp = max(temps, default=None) if temps else None
    temp_val = fmt_temp(temp)

    draw_body_lines_at(draw, 34, [
        (L1, "Used:", used_val),
        (L2, "R/W:", rw_val),
        (L3, "Temp:", temp_val),
    ])


def _fmt_time_short(seconds):
    """Format seconds as compact time string."""
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
