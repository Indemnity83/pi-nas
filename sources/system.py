"""System information data source."""

import socket
import subprocess
import re
from typing import Any, Optional
from sources.base import CachedDataSource


class SystemSource(CachedDataSource):
    """Data source for system information."""

    def _fetch(self, key: str) -> Any:
        """Fetch system data."""
        if key == "ip":
            return self._get_ip_address()
        elif key == "uptime":
            return self._get_uptime_seconds()
        elif key == "power_throttled":
            return self._get_power_throttled()
        elif key == "cpu_temp":
            return self._get_cpu_temp()
        else:
            return None

    def _get_ip_address(self) -> str:
        """Get primary IPv4 address."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "unknown"

    def _get_uptime_seconds(self) -> Optional[float]:
        """Get system uptime in seconds."""
        try:
            with open("/proc/uptime") as f:
                return float(f.read().split()[0])
        except Exception:
            return None

    def _get_power_throttled(self) -> dict:
        """
        Parse Raspberry Pi throttle status flags.

        Returns:
            dict with throttle flags:
                - under_voltage: Currently under-voltage
                - freq_capped: ARM frequency currently capped
                - throttled: Currently throttled
                - soft_temp_limit: Soft temperature limit active
                - under_voltage_occurred: Under-voltage has occurred since boot
                - freq_capped_occurred: Frequency capping has occurred
                - throttled_occurred: Throttling has occurred
                - soft_temp_limit_occurred: Soft temp limit has occurred
                - raw: Raw hex value
        """
        try:
            out = subprocess.check_output(
                ["vcgencmd", "get_throttled"]
            ).decode().strip()
            # 'throttled=0x50005'
            _, hexval = out.split("=")
            val = int(hexval, 16)

            return {
                # Current state (bits 0-3)
                "under_voltage": bool(val & 0x1),
                "freq_capped": bool(val & 0x2),
                "throttled": bool(val & 0x4),
                "soft_temp_limit": bool(val & 0x8),
                # Historical state (bits 16-19)
                "under_voltage_occurred": bool(val & 0x10000),
                "freq_capped_occurred": bool(val & 0x20000),
                "throttled_occurred": bool(val & 0x40000),
                "soft_temp_limit_occurred": bool(val & 0x80000),
                # Raw value
                "raw": hexval,
            }
        except Exception:
            return {
                "under_voltage": False,
                "freq_capped": False,
                "throttled": False,
                "soft_temp_limit": False,
                "under_voltage_occurred": False,
                "freq_capped_occurred": False,
                "throttled_occurred": False,
                "soft_temp_limit_occurred": False,
                "raw": "0x0",
            }

    def _get_cpu_temp(self) -> Optional[float]:
        """Get CPU temperature (Raspberry Pi)."""
        try:
            out = subprocess.check_output(
                ["vcgencmd", "measure_temp"]
            ).decode().strip()
            # 'temp=47.8'C'
            temp = float(out.split("=")[1].split("'")[0])
            return temp
        except Exception:
            return None
