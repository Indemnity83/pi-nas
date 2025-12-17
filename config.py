"""Configuration constants for OLED status display."""

# External services / hardware
GLANCES_URL = "http://localhost:61208/api/4"
I2C_ADDRESS = 0x3C
BUTTON_PIN = 4

# Timing / behavior
NAV_TIMEOUT = 10.0         # seconds before auto-return to "home" page
DATA_INTERVAL = 2.0        # seconds between data polls
DISPLAY_INTERVAL = 0.2     # seconds between OLED refreshes

# Screen geometry
SCREEN_W = 128
SCREEN_H = 64

# Header layout
HEADER_HEIGHT = 16
HEADER_TEXT_X = 0
HEADER_TEXT_Y = 0
HEADER_RIGHT_PADDING = 2
HEADER_ICON_SIZE = 14
HEADER_ICON_Y = (HEADER_HEIGHT - HEADER_ICON_SIZE) // 2
HEADER_ICON_X = SCREEN_W - HEADER_ICON_SIZE - HEADER_RIGHT_PADDING

# Body layout
BODY_TOP = HEADER_HEIGHT
BODY_HEIGHT = SCREEN_H - HEADER_HEIGHT
BODY_CENTER_Y = BODY_TOP + (BODY_HEIGHT // 2)

LINE_HEIGHT = 14
BODY_TEXT_LINES = 3
BODY_TEXT_HEIGHT = LINE_HEIGHT * BODY_TEXT_LINES

BODY_ICON_SIZE = 28
BODY_ICON_Y = BODY_CENTER_Y - (BODY_ICON_SIZE // 2)

L1 = BODY_CENTER_Y - (BODY_TEXT_HEIGHT // 2)
L2 = L1 + LINE_HEIGHT
L3 = L2 + LINE_HEIGHT

# Default mount point for storage
STORAGE_MOUNT = "/mnt/storage"
