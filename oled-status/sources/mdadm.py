"""mdadm/RAID data source."""

import os
import re
import glob
from typing import Any, Optional
from sources.base import CachedDataSource
from config import STORAGE_MOUNT


class MdadmSource(CachedDataSource):
    """Data source for mdadm RAID information."""

    def __init__(self, md_name: Optional[str] = None):
        super().__init__()
        self._md_name = md_name

    @property
    def md_name(self) -> Optional[str]:
        """Get the MD device name, discovering it if needed."""
        if self._md_name is None:
            self._md_name = self._resolve_md_name()
        return self._md_name

    def _fetch(self, key: str) -> Any:
        """Fetch mdadm data."""
        if key == "status":
            return self._get_status()
        elif key == "name":
            return self.md_name
        else:
            return None

    def _resolve_md_name(self, prefer_mountpoint: str = STORAGE_MOUNT) -> Optional[str]:
        """Resolve MD device name from mount point or system."""
        # Best: what backs the mount
        try:
            with open("/proc/mounts") as f:
                for line in f:
                    dev, mnt, *_ = line.split()
                    if mnt == prefer_mountpoint:
                        base = os.path.basename(dev)
                        m = re.match(r"^(md\d+)", base)
                        if m:
                            return m.group(1)
        except Exception:
            pass

        # Next best: /proc/mdstat
        try:
            with open("/proc/mdstat") as f:
                for line in f:
                    m = re.match(r"^(md\d+)\s*:\s*", line)
                    if m:
                        return m.group(1)
        except Exception:
            pass

        # Fallback: /dev/md*
        for path in sorted(glob.glob("/dev/md[0-9]*")):
            return os.path.basename(path)

        return None

    def _get_status(self) -> dict:
        """
        Get raw RAID status and info from sysfs and /proc/mdstat.

        Returns:
            dict with keys:
                array_state: Raw value from /sys/block/{md}/md/array_state
                sync_action: Raw value from /sys/block/{md}/md/sync_action
                progress: Percent complete (float, if available)
                finish_min: Minutes to finish (float, if available)
                speed_kps: Speed in K/sec (float, if available)
        """
        if not self.md_name:
            return {}

        result = {}

        # 1. Array state
        try:
            with open(f"/sys/block/{self.md_name}/md/array_state") as f:
                result["array_state"] = f.read().strip()
        except FileNotFoundError:
            pass

        # 2. Sync action
        try:
            with open(f"/sys/block/{self.md_name}/md/sync_action") as f:
                result["sync_action"] = f.read().strip()
        except FileNotFoundError:
            pass

        # 3. Parse /proc/mdstat for progress info
        sync_action = result.get("sync_action")
        if sync_action and sync_action not in ("idle", "frozen"):
            try:
                with open("/proc/mdstat") as f:
                    mdstat = f.read()

                # Progress percent
                m_pct = re.search(
                    rf"{self.md_name} :.*?(resync|check|recover|recovery)\s*=\s*([\d\.]+)%",
                    mdstat, re.DOTALL
                )
                if m_pct:
                    result["progress"] = float(m_pct.group(2))

                # Finish time
                m_finish = re.search(r"finish=([\d\.]+)min", mdstat)
                if m_finish:
                    result["finish_min"] = float(m_finish.group(1))

                # Speed
                m_speed = re.search(r"speed=([\d\.]+)K/sec", mdstat)
                if m_speed:
                    result["speed_kps"] = float(m_speed.group(1))

            except Exception:
                pass

        return result
