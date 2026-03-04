"""
PiSugar 3 Battery HAT Integration via direct I2C (smbus2).
Kein Daemon nötig - funktioniert auf Pi Zero (ARMv6) ohne Binär-Kompatibilitätsprobleme.

PiSugar 3 I2C-Adresse: 0x57
"""
import threading
import time
import logging
import socket
from typing import Optional, Callable

logger = logging.getLogger(__name__)

PISUGAR3_ADDR = 0x57   # I2C-Adresse PiSugar 3
REG_BATTERY   = 0x2A   # Akku-Prozent (0–100)
REG_STATUS    = 0x02   # Status: Bit7=lädt, Bit0=Button
I2C_BUS       = 1      # /dev/i2c-1
PISUGAR_SOCK  = "/tmp/pisugar-server.sock"


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

    def _query_server(self, command: str) -> Optional[str]:
        """Query local pisugar-server socket if available."""
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.3)
                sock.connect(PISUGAR_SOCK)
                sock.sendall((command.strip() + "\n").encode("utf-8"))
                response = sock.recv(128).decode("utf-8", errors="ignore").strip()
                if not response:
                    return None
                if ":" in response:
                    response = response.split(":", 1)[1].strip()
                return response
        except Exception:
            return None

    def _parse_bool(self, value: Optional[str]) -> Optional[bool]:
        if value is None:
            return None
        v = value.strip().lower()
        if v in ("true", "1", "yes", "on"):
            return True
        if v in ("false", "0", "no", "off"):
            return False
        return None

    def get_battery_level(self) -> Optional[int]:
        """Akku-Stand 0–100%, oder None wenn nicht verfügbar."""
        if self.mock:
            return 75

        server_battery = self._query_server("get battery")
        if server_battery is not None:
            try:
                return max(0, min(100, int(float(server_battery))))
            except Exception:
                pass

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

        # Prefer pisugar-server semantics when available (new models)
        plugged = self._parse_bool(self._query_server("get battery_power_plugged"))
        allow_charging = self._parse_bool(self._query_server("get battery_allow_charging"))
        if plugged is not None and allow_charging is not None:
            return plugged and allow_charging

        charging = self._parse_bool(self._query_server("get battery_charging"))
        if charging is not None:
            return charging

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
