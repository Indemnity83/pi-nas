"""Piezo buzzer hardware control."""

import RPi.GPIO as GPIO
import time


class Buzzer:
    """
    Control piezo buzzer with PWM for tones.

    Assumes active-low trigger (LOW = buzzer on).
    """

    def __init__(self, pin: int, frequency: int = 2000):
        """
        Initialize buzzer.

        Args:
            pin: GPIO pin number (BCM mode)
            frequency: PWM frequency in Hz (default 2000Hz for audible tone)
        """
        self.pin = pin
        self.frequency = frequency
        self.pwm = None

        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.HIGH)  # Start OFF (active-low)

    def beep(self, duration_ms: int = 100, duty_cycle: int = 50):
        """
        Simple beep.

        Args:
            duration_ms: Beep duration in milliseconds
            duty_cycle: PWM duty cycle (0-100)
        """
        self.pwm = GPIO.PWM(self.pin, self.frequency)
        self.pwm.start(duty_cycle)
        time.sleep(duration_ms / 1000.0)
        self.pwm.stop()

    def pattern(self, pattern: str):
        """
        Play a predefined beep pattern.

        Args:
            pattern: Pattern name
                - "short": Single short beep (warning)
                - "long": Single long beep (critical)
                - "double": Two short beeps (attention)
                - "triple": Three short beeps (urgent)
        """
        patterns = {
            "short": [(100, 100)],  # (beep_ms, pause_ms)
            "long": [(500, 100)],
            "double": [(100, 100), (100, 100)],
            "triple": [(100, 100), (100, 100), (100, 100)],
        }

        if pattern not in patterns:
            pattern = "short"

        for beep_ms, pause_ms in patterns[pattern]:
            self.beep(beep_ms)
            time.sleep(pause_ms / 1000.0)

    def cleanup(self):
        """Cleanup GPIO."""
        if self.pwm:
            self.pwm.stop()
        GPIO.output(self.pin, GPIO.HIGH)  # OFF
