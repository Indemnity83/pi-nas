"""Glances API data source."""

import re
import requests
from typing import Any, Optional
from sources.base import CachedDataSource
from config import GLANCES_URL


class GlancesSource(CachedDataSource):
    """
    Data source for Glances monitoring API.

    Simply fetches and caches raw API responses.
    Parsing is left to the consumers (pages).
    """

    def __init__(self, url: str = GLANCES_URL):
        super().__init__()
        self.url = url

    def _fetch(self, endpoint: str) -> Optional[Any]:
        """Fetch data from a Glances API endpoint and parse if needed."""
        try:
            r = requests.get(f"{self.url}/{endpoint}", timeout=2)
            r.raise_for_status()
            data = r.json()

            # Parse SMART data into a more usable structure
            if endpoint == "smart":
                return self._parse_smart_data(data)

            return data
        except Exception:
            return None

    def _parse_smart_data(self, smart_data) -> dict:
        """
        Parse raw SMART data into a cleaner structure.

        Args:
            smart_data: Raw SMART data from Glances API

        Returns:
            dict like: {
                "sda": {
                    "temperature_c": 35.0,
                    "power_on_hours": 12847,
                    "power_cycles": 156,
                    "reallocated_sectors": 0,
                    "pending_sectors": 0,
                    "uncorrectable_sectors": 0,
                    "crc_errors": 0
                }
            }
        """
        parsed = {}

        if not isinstance(smart_data, list):
            return parsed

        for obj in smart_data:
            if not isinstance(obj, dict):
                continue

            # Extract device name
            device_name = obj.get("DeviceName", "")
            if not device_name:
                continue
            dev = device_name.strip().split()[0]
            if not re.fullmatch(r"sd[a-z]+|nvme\d+n\d+|hd[a-z]+", dev):
                continue

            disk_data = {}

            # Temperature (attr 194 or 190)
            temp = self._extract_smart_value(obj, ["194", "190"], name_filter="temp")
            if temp is not None:
                disk_data["temperature_c"] = temp

            # Power on hours (attr 9)
            poh = self._extract_smart_value(obj, ["9"])
            if poh is not None:
                disk_data["power_on_hours"] = int(poh)

            # Power cycles (attr 12)
            pc = self._extract_smart_value(obj, ["12"])
            if pc is not None:
                disk_data["power_cycles"] = int(pc)

            # Reallocated sectors (attr 5)
            rs = self._extract_smart_value(obj, ["5"])
            if rs is not None:
                disk_data["reallocated_sectors"] = int(rs)

            # Pending sectors (attr 197)
            ps = self._extract_smart_value(obj, ["197"])
            if ps is not None:
                disk_data["pending_sectors"] = int(ps)

            # Uncorrectable sectors (attr 198)
            us = self._extract_smart_value(obj, ["198"])
            if us is not None:
                disk_data["uncorrectable_sectors"] = int(us)

            # CRC errors (attr 199)
            crc = self._extract_smart_value(obj, ["199"])
            if crc is not None:
                disk_data["crc_errors"] = int(crc)

            if disk_data:
                parsed[dev] = disk_data

        return parsed

    def _extract_smart_value(self, obj: dict, attr_ids: list, name_filter: str = None) -> Optional[float]:
        """
        Extract a SMART attribute value.

        Args:
            obj: SMART data object for a disk
            attr_ids: List of attribute IDs to check (e.g., ["194", "190"])
            name_filter: Optional string that must be in attribute name (e.g., "temp")

        Returns:
            Raw value as float, or None if not found
        """
        for attr_id in attr_ids:
            a = obj.get(attr_id)
            if isinstance(a, dict):
                # Check name filter if provided
                if name_filter:
                    name = (a.get("name") or "").lower()
                    if name_filter.lower() not in name:
                        continue

                raw = a.get("raw")
                if raw is not None:
                    # Extract first number from raw value
                    m = re.search(r"(-?\d+(\.\d+)?)", str(raw))
                    if m:
                        return float(m.group(1))

        return None
