"""Page modules for OLED display."""

from pages.home import render as home
from pages.network import render as network
from pages.system import render as system
from pages.storage import render as storage
from pages.raid import render as raid
from pages.temps import render as temps

# List of browsable pages (excludes home which is auto-displayed)
BROWSE_PAGES = [network, system, storage, raid, temps]
