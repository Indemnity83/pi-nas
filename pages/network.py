"""Network page."""

from render import draw_header, draw_body_line, draw_body_text, fmt_rate, fmt_two_cols, fmt_time
from config import L1, L2, L3


def render(draw, ctx):
    """Render network page."""
    draw_header(draw, ctx, "Network")

    ip = ctx.system.get("ip", ttl_s=30.0)

    # Network rates for eth0
    net_list = ctx.glances.get("network", ttl_s=2.0) or []
    tx_kbps = rx_kbps = 0.0
    for n in net_list:
        if n.get("interface_name") == "eth0":
            tx_kbps = n.get("bytes_sent_rate_per_sec", 0) / 1024
            rx_kbps = n.get("bytes_recv_rate_per_sec", 0) / 1024
            break

    tx = fmt_rate(tx_kbps)
    rx = fmt_rate(rx_kbps)
    rate = fmt_two_cols("▲", tx, "▼", rx)

    uptime_val = fmt_time(ctx.system.get("uptime", ttl_s=10.0))

    draw_body_line(draw, L1, "IP:", ip)
    draw_body_text(draw, L2, rate)
    draw_body_line(draw, L3, "Uptime:", uptime_val)
