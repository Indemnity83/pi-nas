"""Alarm monitoring and alerting."""

import time


class AlarmState:
    """Track alarm state to prevent repeated beeping."""

    def __init__(self, cooldown_seconds: float = 60.0):
        """
        Initialize alarm state.

        Args:
            cooldown_seconds: Minimum time between repeated alarms
        """
        self.cooldown = cooldown_seconds
        self.last_alert = {}  # alarm_id -> timestamp

    def should_alert(self, alarm_id: str) -> bool:
        """
        Check if enough time has passed since last alert.

        Args:
            alarm_id: Unique alarm identifier

        Returns:
            True if alarm should trigger, False if in cooldown
        """
        now = time.time()
        last = self.last_alert.get(alarm_id, 0)

        if now - last >= self.cooldown:
            self.last_alert[alarm_id] = now
            return True

        return False

    def clear(self, alarm_id: str):
        """Clear alarm state (alarm condition resolved)."""
        self.last_alert.pop(alarm_id, None)


# Global alarm state
_alarm_state = AlarmState(cooldown_seconds=300.0)  # 5 minute cooldown


def check(ctx, buzzer):
    """
    Check alarm conditions and alert if needed.

    Called from main loop each iteration. Similar to page render() but
    evaluates conditions and triggers buzzer instead of drawing.

    Args:
        ctx: Data context
        buzzer: Buzzer instance
    """
    # Check RAID status
    raid_status = ctx.mdadm.get("status", ttl_s=5.0)
    array_state = raid_status.get("array_state", "")
    sync_action = raid_status.get("sync_action", "")

    # RAID degraded - double beep
    if "degraded" in array_state.lower():
        if _alarm_state.should_alert("raid_degraded"):
            buzzer.pattern("double")

    # RAID recovering/resyncing - single short beep (informational)
    elif sync_action in ("resync", "recovery", "recover"):
        # Only alert once when resync starts
        if _alarm_state.should_alert("raid_resync"):
            buzzer.pattern("short")
    else:
        # RAID healthy - clear any previous alarms
        _alarm_state.clear("raid_degraded")
        _alarm_state.clear("raid_resync")

    # Check disk temperatures
    smart = ctx.glances.get("smart", ttl_s=10.0) or {}

    for disk, data in smart.items():
        temp = data.get("temperature_c")
        if temp is None:
            continue

        alarm_id = f"temp_{disk}"

        # Critical temperature - triple beep
        if temp >= 60.0:
            if _alarm_state.should_alert(alarm_id):
                buzzer.pattern("triple")

        # Warning temperature - single beep
        elif temp >= 50.0:
            if _alarm_state.should_alert(alarm_id):
                buzzer.pattern("short")
        else:
            # Temperature normal - clear alarm
            _alarm_state.clear(alarm_id)

    # Check for bad sectors (critical SMART attributes)
    for disk, data in smart.items():
        reallocated = data.get("reallocated_sectors", 0)
        pending = data.get("pending_sectors", 0)
        uncorrectable = data.get("uncorrectable_sectors", 0)

        alarm_id = f"smart_{disk}"

        # Any bad sectors - long beep
        if reallocated > 0 or pending > 0 or uncorrectable > 0:
            if _alarm_state.should_alert(alarm_id):
                buzzer.pattern("long")
        else:
            _alarm_state.clear(alarm_id)

    # Check power throttling
    throttle = ctx.system.get("power_throttled", ttl_s=10.0)
    if throttle.get("under_voltage") or throttle.get("throttled"):
        if _alarm_state.should_alert("power_throttle"):
            buzzer.pattern("double")
    else:
        _alarm_state.clear("power_throttle")
