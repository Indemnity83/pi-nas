"""Matrix-style screensaver for OLED display."""

import random
from config import SCREEN_W, SCREEN_H, HEADER_HEIGHT, BODY_TOP
from hardware.display import (
    CLEAN_FRAME, DEGRADED_FRAMES, REBUILD_FRAMES, UNKNOWN_FRAMES,
    Display
)

# Matrix characters (numbers, letters, symbols that work in FiraCode)
MATRIX_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()_+-=[]{}|;:,.<>?/"


class MatrixRain:
    """Dynamic Matrix rain screensaver with falling characters."""

    def __init__(self, font, char_width=8, char_height=14):
        """
        Initialize Matrix rain state.

        Args:
            font: PIL font to use for rendering
            char_width: Width of each character column in pixels
            char_height: Height of each character in pixels
        """
        self.font = font
        self.char_width = char_width
        self.char_height = char_height

        # Calculate number of character columns
        self.num_columns = SCREEN_W // char_width
        self.columns = []

        # Initialize random drops in each column
        for _ in range(self.num_columns):
            self.columns.append({
                'y': random.randint(-5, 8),           # Character position (in chars, not pixels)
                'length': random.randint(3, 8),       # Length of the drop trail (in chars)
                'speed': random.choice([0.5, 1.0]),   # Fall speed (chars per frame)
                'active': random.random() < 0.3,      # 30% chance column is active
                'chars': self._random_chars(8),       # Random characters for this drop
                'char_age': 0                         # Frames since last char change
            })

    def _random_chars(self, length):
        """Generate random Matrix characters."""
        return [random.choice(MATRIX_CHARS) for _ in range(length)]

    def update(self):
        """Update drop positions and randomize characters."""
        for col in self.columns:
            if col['active']:
                col['y'] += col['speed']
                col['char_age'] += 1

                # Randomize some characters periodically
                if col['char_age'] > 2:
                    col['char_age'] = 0
                    # Change a few random characters
                    for _ in range(random.randint(1, 3)):
                        idx = random.randint(0, len(col['chars']) - 1)
                        col['chars'][idx] = random.choice(MATRIX_CHARS)

                # If drop has fallen off screen, reset it
                if col['y'] > (SCREEN_H // self.char_height) + col['length']:
                    col['y'] = -col['length']
                    col['length'] = random.randint(3, 8)
                    col['speed'] = random.choice([0.5, 1.0])
                    col['chars'] = self._random_chars(8)
                    # 20% chance to deactivate when resetting
                    col['active'] = random.random() > 0.2
            else:
                # Inactive columns: small chance to activate
                if random.random() < 0.02:
                    col['active'] = True
                    col['y'] = -col['length']
                    col['chars'] = self._random_chars(8)

    def render(self, draw):
        """Render Matrix rain to display with actual characters."""
        for col_idx, col in enumerate(self.columns):
            if not col['active']:
                continue

            x_pos = col_idx * self.char_width
            y_pos = col['y']
            length = col['length']

            # Draw the character trail
            for i in range(int(length)):
                char_y = int((y_pos - i) * self.char_height)

                # Skip if off screen
                if char_y < -self.char_height or char_y >= SCREEN_H:
                    continue

                # Get character to display (cycle through the random chars)
                char = col['chars'][i % len(col['chars'])]

                # Only render head and first few chars brightly
                # Skip some tail chars for fade effect
                if i == 0:
                    # Bright head - always render
                    draw.text((x_pos, char_y), char, font=self.font, fill=255)
                elif i < 3:
                    # Bright section
                    draw.text((x_pos, char_y), char, font=self.font, fill=255)
                elif i % 2 == 0:
                    # Fading tail (sparse)
                    draw.text((x_pos, char_y), char, font=self.font, fill=255)


class BouncingRaidIcon:
    """Bouncing DVD-style screensaver using RAID status icon."""

    ICON_SIZE = 28  # RAID icons are 14x14, scaled 2x = 28x28

    def __init__(self):
        """Initialize bouncing RAID icon."""
        # Start at random position (constrained to body area)
        self.x = random.randint(0, SCREEN_W - self.ICON_SIZE)
        self.y = random.randint(BODY_TOP, SCREEN_H - self.ICON_SIZE)

        # Random velocity (1-2 pixels per frame, in both x and y)
        self.vx = random.choice([-2, -1, 1, 2])
        self.vy = random.choice([-2, -1, 1, 2])

    def _get_raid_icon(self, ctx):
        """Get the appropriate RAID icon based on current status."""
        # Always use clean icon for screensaver
        # (screensaver only activates when RAID is clean)
        return CLEAN_FRAME

    def update(self):
        """Update icon position and bounce off walls."""
        # Move icon
        self.x += self.vx
        self.y += self.vy

        # Bounce off edges (constrain to body area)
        if self.x <= 0:
            self.x = 0
            self.vx = abs(self.vx)  # Bounce right
        elif self.x >= SCREEN_W - self.ICON_SIZE:
            self.x = SCREEN_W - self.ICON_SIZE
            self.vx = -abs(self.vx)  # Bounce left

        # Constrain y to body area only
        if self.y <= BODY_TOP:
            self.y = BODY_TOP
            self.vy = abs(self.vy)  # Bounce down
        elif self.y >= SCREEN_H - self.ICON_SIZE:
            self.y = SCREEN_H - self.ICON_SIZE
            self.vy = -abs(self.vy)  # Bounce up

    def render(self, draw, ctx):
        """Render the bouncing RAID icon (scaled 2x)."""
        # Draw bouncing icon
        icon = self._get_raid_icon(ctx)
        for dx, dy in icon:
            # Scale 2x like the big icons on status pages
            px = self.x + dx * 2
            py = self.y + dy * 2
            draw.rectangle((px, py, px + 1, py + 1), outline=255, fill=255)
