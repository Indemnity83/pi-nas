"""Button hardware control."""

import RPi.GPIO as GPIO
from config import BUTTON_PIN


class Button:
    """Button input hardware control."""

    def __init__(self):
        """Initialize Button instance."""
        self._initialized = False

    @classmethod
    def init(cls, callback):
        """
        Initialize button GPIO and register callback.

        Args:
            callback: Function to call on button press (receives channel parameter)

        Returns:
            Button instance
        """
        instance = cls()

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(
            BUTTON_PIN,
            GPIO.FALLING,
            callback=callback,
            bouncetime=250
        )
        instance._initialized = True
        return instance

    def cleanup(self):
        """Cleanup GPIO resources."""
        if self._initialized:
            GPIO.cleanup()
            self._initialized = False
