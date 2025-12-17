#!/usr/bin/env python3
"""Main entry point for OLED status display."""

import RPi.GPIO as GPIO
import time
import signal
import sys
from PIL import Image, ImageDraw

from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306

from config import I2C_ADDRESS, BUTTON_PIN, BUZZER_PIN, NAV_TIMEOUT, DISPLAY_INTERVAL
from context import Context
from render import FONT, advance_spin_frame
from buzzer import Buzzer
import pages
import alarms


# Global state
current_page = -1     # -1 means "home mode"
last_nav_at = 0.0     # monotonic timestamp of last navigation
ctx = None            # Global context
device = None         # Global device
buzzer = None         # Global buzzer


def on_button(channel):
    """Handle button press."""
    global current_page, last_nav_at

    now = time.monotonic()
    last_nav_at = now

    # If in home mode, start at first browse page
    if current_page == -1:
        current_page = 0
    else:
        current_page = (current_page + 1) % len(pages.BROWSE_PAGES)


def gpio_init():
    """Initialize GPIO for button input."""
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(
        BUTTON_PIN,
        GPIO.FALLING,
        callback=on_button,
        bouncetime=250
    )


def draw_loading_screen(device, text="Loading…"):
    """Show loading message on display."""
    from config import SCREEN_W, BODY_CENTER_Y, LINE_HEIGHT
    from render import FONT, text_width

    image = Image.new("1", (device.width, device.height))
    draw = ImageDraw.Draw(image)

    try:
        w = int(FONT.getlength(text))
    except Exception:
        bbox = draw.textbbox((0, 0), text, font=FONT)
        w = bbox[2] - bbox[0]

    x = (SCREEN_W - w) // 2
    y = BODY_CENTER_Y - (LINE_HEIGHT // 2)

    draw.text((x, y), text, font=FONT, fill=255)
    device.display(image)


def draw_fatal_error(device, line1, line2=None):
    """Show fatal error on display."""
    from config import L2, L3
    from render import FONT

    image = Image.new("1", (device.width, device.height))
    draw = ImageDraw.Draw(image)

    draw.text((0, L2), line1, font=FONT, fill=255)
    if line2:
        draw.text((0, L3), line2, font=FONT, fill=255)

    device.display(image)


def clear_display(device):
    """Clear the display."""
    image = Image.new("1", (device.width, device.height))
    device.display(image)


def handle_shutdown(signum, frame):
    """Handle shutdown signals."""
    global device, buzzer
    if device:
        clear_display(device)
    if buzzer:
        buzzer.cleanup()
    GPIO.cleanup()
    sys.exit(0)


def main():
    """Main loop."""
    global current_page, last_nav_at, ctx, device, buzzer

    # Initialize hardware
    serial = i2c(port=1, address=I2C_ADDRESS)
    device = ssd1306(serial, width=128, height=64)

    draw_loading_screen(device, "Loading...")

    # Setup signal handlers
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    # Initialize context
    ctx = Context()

    # Check RAID is available
    md_name = ctx.mdadm.get("name")
    if not md_name:
        from config import STORAGE_MOUNT
        draw_fatal_error(device, "RAID not found", STORAGE_MOUNT)
        time.sleep(5)
        clear_display(device)
        return

    # Initialize GPIO
    gpio_init()

    # Initialize buzzer
    buzzer = Buzzer(BUZZER_PIN)

    # Main loop
    while True:
        now_mono = time.monotonic()

        # Check alarms (before display updates)
        alarms.check(ctx, buzzer)

        # Auto-return to home if user hasn't navigated recently
        if current_page != -1 and (now_mono - last_nav_at) >= NAV_TIMEOUT:
            current_page = -1

        # Advance animation frame
        advance_spin_frame()

        # Render
        image = Image.new("1", (device.width, device.height))
        draw = ImageDraw.Draw(image)

        # Copy to avoid race conditions
        page = current_page
        nav_at = last_nav_at

        try:
            if page == -1 or (now_mono - nav_at) >= NAV_TIMEOUT:
                # Home page
                pages.home(draw, ctx)
            else:
                # Browse page
                pages.BROWSE_PAGES[page](draw, ctx)
        except Exception as e:
            # Error display
            draw.text((0, 0), "OLED ERR", font=FONT, fill=255)
            draw.text((0, 16), str(e)[:20], font=FONT, fill=255)

        device.display(image)
        time.sleep(DISPLAY_INTERVAL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        try:
            if device:
                clear_display(device)
        except Exception:
            pass
        try:
            if buzzer:
                buzzer.cleanup()
        except Exception:
            pass
        GPIO.cleanup()
