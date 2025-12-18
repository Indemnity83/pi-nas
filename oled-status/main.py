#!/usr/bin/env python3
"""Main entry point for OLED status display."""

import time
import signal
import sys

from config import NAV_TIMEOUT, DISPLAY_INTERVAL
from context import Context
from hardware.display import Display
from hardware.button import Button
from hardware.buzzer import Buzzer
import pages
import alarms


# Global state
current_page = -1     # -1 means "home mode"
last_nav_at = 0.0     # monotonic timestamp of last navigation
ctx = None            # Global context
display = None        # Global display
button = None         # Global button
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


def handle_shutdown(signum, frame):
    """Handle shutdown signals."""
    global display, button, buzzer
    if display:
        display.clear()
    if buzzer:
        buzzer.cleanup()
    if button:
        button.cleanup()
    sys.exit(0)


def main():
    """Main loop."""
    global current_page, last_nav_at, ctx, display, button, buzzer

    # Initialize display
    display = Display.init()
    display.draw_loading_screen("Loading...")

    # Setup signal handlers
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    # Initialize context
    ctx = Context()

    # Check RAID is available
    md_name = ctx.mdadm.get("name")
    if not md_name:
        from config import STORAGE_MOUNT
        display.draw_fatal_error("RAID not found", STORAGE_MOUNT)
        time.sleep(5)
        display.clear()
        return

    # Initialize button
    button = Button.init(on_button)

    # Initialize buzzer
    buzzer = Buzzer.init()

    # Initialize last navigation time to now (prevent immediate screensaver)
    last_nav_at = time.monotonic()

    # Main loop
    while True:
        now_mono = time.monotonic()

        # Check alarms (before display updates)
        alarms.check(ctx, buzzer)

        # Auto-return to home if user hasn't navigated recently
        if current_page != -1 and (now_mono - last_nav_at) >= NAV_TIMEOUT:
            current_page = -1

        # Advance animation frame
        Display.advance_frame()

        # Copy to avoid race conditions
        page = current_page
        nav_at = last_nav_at

        # Add navigation timing to context for pages that need it
        ctx.last_nav_at = nav_at

        # Render page
        try:
            if page == -1 or (now_mono - nav_at) >= NAV_TIMEOUT:
                # Home page (handles screensaver internally)
                display.render(pages.home, ctx)
            else:
                # Browse page
                display.render(pages.BROWSE_PAGES[page], ctx)
        except Exception as e:
            # Error display
            display.show_error(str(e))

        time.sleep(DISPLAY_INTERVAL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        try:
            if display:
                display.clear()
        except Exception:
            pass
        try:
            if buzzer:
                buzzer.cleanup()
        except Exception:
            pass
        try:
            if button:
                button.cleanup()
        except Exception:
            pass
