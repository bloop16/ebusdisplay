"""
PiSugar 3 Battery HAT Integration via direct I2C (smbus2).
Kein Daemon nötig - funktioniert auf Pi Zero (ARMv6) ohne Binär-Kompatibilitätsprobleme.

PiSugar 3 I2C-Adresse: 0x57
"""
import threading
import time
import logging
from typing import Optional, Callable

logger = logging.getLogger(__name__)

PISUGAR3_ADDR = 0x57   # I2C-Adresse PiSugar 3
REG_BATTERY   = 0x2A   # Akku-Prozent (0–100)
REG_STATUS    = 0x02   # Status: Bit7=lädt, Bit0=Button
I2C_BUS       = 1      # /dev/i2c-1


class PiSugar:
    """PiSugar 3 via I2C – kein pisugar-server Daemon erforderlich."""

    def __init__(self, mock=False):
        self.mock = mock
        self.available = False
        self._bus = None
        self._button_callback: Optional[Callable] = None
        self._stop_event = threading.Event()
        self._button_thread: Optional[threading.Thread] = None

        if not mock:
            self._init_i2c()

    def _init_i2c(self):
        try:
            import smbus2
            self._bus = smbus2.SMBus(I2C_BUS)
            # Verbindung testen
            self._bus.read_byte_data(PISUGAR3_ADDR, REG_BATTERY)
            self.available = True
            logger.info("PiSugar 3 erkannt (I2C direkt)")
        except Exception as e:
            logger.warning(f"PiSugar nicht erkannt: {e}")
            self.available = False

    def get_battery_level(self) -> Optional[int]:
        """Akku-Stand 0–100%, oder None wenn nicht verfügbar."""
        if self.mock:
            return 75
        if not self.available:
            return None
        try:
            val = self._bus.read_byte_data(PISUGAR3_ADDR, REG_BATTERY)
            return max(0, min(100, val))
        except Exception:
            return None

    def is_charging(self) -> bool:
        """True wenn USB-Strom angeschlossen."""
        if self.mock:
            return False
        if not self.available:
            return True  # ohne Akku → AC-Betrieb annehmen
        try:
            status = self._bus.read_byte_data(PISUGAR3_ADDR, REG_STATUS)
            return bool(status & 0x80)
        except Exception:
            return True

    def register_button_callback(self, callback: Callable):
        """Button-Callback registrieren. Wird in Hintergrund-Thread gepollt."""
        self._button_callback = callback
        if self.mock:
            logger.info("[MOCK] Button callback registriert")
            return
        if not self.available:
            logger.warning("PiSugar nicht verfügbar, kein Button-Callback")
            return
        self._stop_event.clear()
        self._button_thread = threading.Thread(
            target=self._poll_button, daemon=True, name="pisugar-btn"
        )
        self._button_thread.start()
        logger.info("PiSugar Button-Polling gestartet (I2C)")

    def _poll_button(self):
        """Button-Status alle 300ms per I2C lesen, Flanke erkennen."""
        prev = False
        while not self._stop_event.is_set():
            try:
                status = self._bus.read_byte_data(PISUGAR3_ADDR, REG_STATUS)
                pressed = bool(status & 0x01)
                if pressed and not prev:
                    logger.info("Button gedrückt (I2C)")
                    if self._button_callback:
                        self._button_callback()
                prev = pressed
            except Exception as e:
                logger.debug(f"Button poll Fehler: {e}")
            time.sleep(0.3)

    def stop(self):
        """Polling-Thread stoppen."""
        self._stop_event.set()
        if self._bus:
            try:
                self._bus.close()
            except Exception:
                pass

    def get_status_dict(self) -> dict:
        return {
            'battery_level': self.get_battery_level(),
            'charging': self.is_charging(),
            'available': self.available or self.mock,
        }
