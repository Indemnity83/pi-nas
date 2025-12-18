"""Context object providing access to all data sources."""

from sources.glances import GlancesSource
from sources.mdadm import MdadmSource
from sources.system import SystemSource


class Context:
    """
    Central context providing access to all data sources.

    Usage:
        ctx = Context()
        cpu = ctx.glances.get("cpu_percent", ttl_s=2.0)
        raid = ctx.mdadm.get("status", ttl_s=5.0)
        ip = ctx.system.get("ip", ttl_s=30.0)
    """

    def __init__(self):
        self.glances = GlancesSource()
        self.mdadm = MdadmSource()
        self.system = SystemSource()

    def invalidate_all(self):
        """Clear all caches across all data sources."""
        self.glances.invalidate()
        self.mdadm.invalidate()
        self.system.invalidate()
