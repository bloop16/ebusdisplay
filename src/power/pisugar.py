"""
PiSugar Battery HAT Integration
Monitors battery level and handles button press events.
"""
import subprocess
import logging
import time
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class PiSugar:
    """Interface to PiSugar battery HAT"""
    
    def __init__(self, mock=False):
        """
        Initialize PiSugar interface.
        
        Args:
            mock: If True, return simulated values (for testing)
        """
        self.mock = mock
        self.available = False
        
        if not mock:
            self.available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """Check if PiSugar is available"""
        try:
            # Try to read battery level
            result = subprocess.run(
                ['cat', '/sys/class/power_supply/pisugar-battery/capacity'],
                capture_output=True,
                text=True,
                timeout=1
            )
            return result.returncode == 0
        except:
            logger.warning("PiSugar not detected")
            return False
    
    def get_battery_level(self) -> Optional[int]:
        """
        Get battery level (0-100%).
        
        Returns:
            Battery percentage or None if unavailable
        """
        if self.mock:
            return 75  # Mock value
        
        if not self.available:
            return None
        
        try:
            result = subprocess.run(
                ['cat', '/sys/class/power_supply/pisugar-battery/capacity'],
                capture_output=True,
                text=True,
                timeout=1
            )
            
            if result.returncode == 0:
                return int(result.stdout.strip())
            
        except Exception as e:
            logger.error(f"Failed to read battery level: {e}")
        
        return None
    
    def is_charging(self) -> bool:
        """
        Check if battery is charging (AC power connected).
        
        Returns:
            True if AC power connected
        """
        if self.mock:
            return False  # Mock: on battery
        
        if not self.available:
            return True  # Assume AC if no battery detected
        
        try:
            result = subprocess.run(
                ['cat', '/sys/class/power_supply/pisugar-battery/status'],
                capture_output=True,
                text=True,
                timeout=1
            )
            
            if result.returncode == 0:
                status = result.stdout.strip().lower()
                return status in ['charging', 'full']
            
        except Exception as e:
            logger.error(f"Failed to read charging status: {e}")
        
        return True  # Default: assume AC power
    
    def get_voltage(self) -> Optional[float]:
        """
        Get battery voltage in volts.
        
        Returns:
            Voltage or None if unavailable
        """
        if self.mock:
            return 3.7  # Mock value
        
        if not self.available:
            return None
        
        try:
            result = subprocess.run(
                ['cat', '/sys/class/power_supply/pisugar-battery/voltage_now'],
                capture_output=True,
                text=True,
                timeout=1
            )
            
            if result.returncode == 0:
                # Value is in microvolts
                microvolts = int(result.stdout.strip())
                return microvolts / 1_000_000.0
            
        except Exception as e:
            logger.error(f"Failed to read voltage: {e}")
        
        return None
    
    def register_button_callback(self, callback: Callable):
        """
        Register callback for button press events.
        
        Args:
            callback: Function to call when button is pressed
        """
        # PiSugar button handling via GPIO
        # GPIO pin for button: check PiSugar docs
        # This is a simplified implementation
        
        if self.mock:
            logger.info("[MOCK] Button callback registered")
            return
        
        try:
            import RPi.GPIO as GPIO
            
            BUTTON_PIN = 4  # Check PiSugar documentation
            
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            def button_pressed(channel):
                logger.info("Button pressed!")
                callback()
            
            GPIO.add_event_detect(
                BUTTON_PIN,
                GPIO.FALLING,
                callback=button_pressed,
                bouncetime=300
            )
            
            logger.info("Button callback registered")
            
        except Exception as e:
            logger.error(f"Failed to register button callback: {e}")
    
    def get_status_dict(self) -> dict:
        """
        Get complete power status as dictionary.
        
        Returns:
            Dictionary with battery_level, charging, voltage
        """
        return {
            'battery_level': self.get_battery_level(),
            'charging': self.is_charging(),
            'voltage': self.get_voltage(),
            'available': self.available or self.mock
        }


def main():
    """Test PiSugar interface"""
    logging.basicConfig(level=logging.INFO)
    
    # Test with mock mode
    pisugar = PiSugar(mock=True)
    
    print("=== PiSugar Status ===")
    status = pisugar.get_status_dict()
    
    print(f"Available: {status['available']}")
    print(f"Battery Level: {status['battery_level']}%")
    print(f"Charging: {status['charging']}")
    print(f"Voltage: {status['voltage']}V")
    
    # Test button callback
    def on_button_press():
        print("Button pressed! Updating display...")
    
    pisugar.register_button_callback(on_button_press)
    
    if pisugar.mock:
        print("\n[MOCK MODE] Simulating button press...")
        on_button_press()


if __name__ == '__main__':
    main()
