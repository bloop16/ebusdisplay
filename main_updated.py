#!/usr/bin/env python3
"""
Main controller for Bus Display with PiSugar support.
"""
import time
import json
import logging
from pathlib import Path
from datetime import datetime

from src.api import VMobilAPI
from src.display.renderer import DisplayRenderer
from src.display.driver import DisplayDriver
from src.power.pisugar import PiSugar

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BusDisplay:
    """Main controller with battery awareness"""
    
    def __init__(self, config_path='config/stops.json', mock_display=False, mock_battery=False):
        self.config_path = Path(config_path)
        self.mock_display = mock_display
        
        logger.info("Initializing Bus Display...")
        
        # Initialize components
        self.api = VMobilAPI()
        self.renderer = DisplayRenderer()
        self.display = DisplayDriver(mock=mock_display)
        self.pisugar = PiSugar(mock=mock_battery)
        
        # Load configuration
        self.stops = []
        self.load_config()
        
        # Button press flag
        self.button_pressed = False
        
        # Register button callback
        self.pisugar.register_button_callback(self.on_button_press)
        
        logger.info(f"Bus Display initialized ({len(self.stops)} stops, battery: {self.pisugar.available})")
    
    def on_button_press(self):
        """Handle PiSugar button press"""
        logger.info("Button pressed - triggering update")
        self.button_pressed = True
        
        # Immediate update
        self.update_display()
    
    def load_config(self):
        """Load stop configuration"""
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    config = json.load(f)
                    self.stops = config.get('stops', [])
                logger.info(f"Loaded {len(self.stops)} stops from config")
            except Exception as e:
                logger.error(f"Config load failed: {e}")
                self.stops = []
        else:
            logger.warning("No config file found")
    
    def update_display(self):
        """Fetch departures and update display"""
        if not self.stops:
            logger.warning("No stops configured")
            self._show_setup_message()
            return
        
        stop = self.stops[0]
        logger.info(f"Fetching departures for {stop['name']}...")
        
        try:
            # Fetch departures
            departures = self.api.get_departures(stop_id=stop['id'], limit=4)
            
            if not departures:
                logger.warning("No departures found")
            else:
                logger.info(f"Got {len(departures)} departures")
            
            # Get battery status
            battery_level = self.pisugar.get_battery_level()
            if battery_level is not None:
                logger.info(f"Battery: {battery_level}%")
            
            # Render to image
            image = self.renderer.render_departures(
                departures,
                stop['name'],
                battery_percent=battery_level,
                wifi_connected=True
            )
            
            # Display
            self.display.display_image(image)
            logger.info("Display updated successfully")
            
            # Reset button flag
            self.button_pressed = False
            
        except Exception as e:
            logger.error(f"Update failed: {e}")
            self._show_error_message(str(e))
    
    def _show_setup_message(self):
        """Show setup instructions"""
        from PIL import Image, ImageDraw, ImageFont
        
        image = Image.new('1', (250, 122), 255)
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        
        draw.text((10, 40), "No stops configured", font=font, fill=0)
        draw.text((10, 60), "Visit http://bus-display:5000", font=font, fill=0)
        
        self.display.display_image(image)
    
    def _show_error_message(self, error: str):
        """Show error message"""
        from PIL import Image, ImageDraw, ImageFont
        
        image = Image.new('1', (250, 122), 255)
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        
        draw.text((10, 40), "Error:", font=font, fill=0)
        draw.text((10, 60), error[:30], font=font, fill=0)
        
        self.display.display_image(image)
    
    def run_once(self):
        """Single update"""
        logger.info("=== Running single update ===")
        self.update_display()
    
    def run_continuous(self, interval_minutes=5):
        """Continuous mode with battery awareness"""
        logger.info(f"=== Continuous mode (interval: {interval_minutes}min) ===")
        
        # Check power mode
        is_charging = self.pisugar.is_charging()
        
        if is_charging:
            logger.info("AC power detected - auto-update mode")
            mode = "auto"
        else:
            logger.info("Battery mode - button-triggered updates")
            mode = "button"
        
        while True:
            try:
                if mode == "auto":
                    # AC power: auto-update
                    self.update_display()
                    logger.info(f"Sleeping {interval_minutes} minutes...")
                    time.sleep(interval_minutes * 60)
                    
                elif mode == "button":
                    # Battery: wait for button press
                    if self.button_pressed:
                        self.update_display()
                    
                    # Sleep briefly and check button
                    time.sleep(1)
                
            except KeyboardInterrupt:
                logger.info("Interrupted by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                time.sleep(60)


def main():
    """Entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Bus Display Controller')
    parser.add_argument('--mock-display', action='store_true', help='Mock display')
    parser.add_argument('--mock-battery', action='store_true', help='Mock battery')
    parser.add_argument('--continuous', action='store_true', help='Continuous mode')
    parser.add_argument('--interval', type=int, default=5, help='Update interval (min)')
    
    args = parser.parse_args()
    
    try:
        display = BusDisplay(
            mock_display=args.mock_display,
            mock_battery=args.mock_battery
        )
        
        if args.continuous:
            display.run_continuous(interval_minutes=args.interval)
        else:
            display.run_once()
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
