"""Formatting utilities for display values."""


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


def fmt_label_value(label: str, value: str, body_cols: int) -> str:
    """Return string with label left-aligned and value right-aligned."""
    label = str(label)
    value = str(value)
    total_len = len(label) + len(value)
    if total_len >= body_cols:
        return label + value
    spaces = body_cols - total_len
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
    total_cols: int,
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
