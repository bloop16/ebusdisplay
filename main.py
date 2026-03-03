#!/usr/bin/env python3
"""
Main controller for Bus Display.
Coordinates API, display, and power management.
"""
import time
import json
import logging
from pathlib import Path
from datetime import datetime

from src.api import VMobilAPI
from src.display.renderer import DisplayRenderer
from src.display.driver import DisplayDriver

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BusDisplay:
    """Main controller for bus display"""
    
    def __init__(self, config_path='config/stops.json', mock_display=False):
        self.config_path = Path(config_path)
        self.mock_display = mock_display
        
        # Initialize components
        logger.info("Initializing Bus Display...")
        self.api = VMobilAPI()
        self.renderer = DisplayRenderer()
        self.display = DisplayDriver(mock=mock_display)
        
        # Load configuration
        self.stops = []
        self.load_config()
        
        logger.info(f"Bus Display initialized ({len(self.stops)} stops configured)")
    
    def load_config(self):
        """Load stop configuration from JSON file"""
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
        
        # Use first stop for now (TODO: rotation or combined view)
        stop = self.stops[0]
        logger.info(f"Fetching departures for {stop['name']}...")
        
        try:
            # Fetch departures
            departures = self.api.get_departures(stop_id=stop['id'], limit=4)
            
            if not departures:
                logger.warning("No departures found")
            else:
                logger.info(f"Got {len(departures)} departures")
            
            # Render to image
            image = self.renderer.render_departures(
                departures,
                stop['name'],
                battery_percent=None,  # TODO: Get from PiSugar
                wifi_connected=True     # TODO: Check actual WiFi status
            )
            
            # Display on e-ink
            self.display.display_image(image)
            logger.info("Display updated successfully")
            
        except Exception as e:
            logger.error(f"Update failed: {e}")
            self._show_error_message(str(e))
    
    def _show_setup_message(self):
        """Show setup instructions on display"""
        from PIL import Image, ImageDraw, ImageFont
        
        image = Image.new('1', (250, 122), 255)
        draw = ImageDraw.Draw(image)
        
        font = ImageFont.load_default()
        
        draw.text((10, 40), "No stops configured", font=font, fill=0)
        draw.text((10, 60), "Visit http://192.168.x.x:5000", font=font, fill=0)
        
        self.display.display_image(image)
    
    def _show_error_message(self, error: str):
        """Show error message on display"""
        from PIL import Image, ImageDraw, ImageFont
        
        image = Image.new('1', (250, 122), 255)
        draw = ImageDraw.Draw(image)
        
        font = ImageFont.load_default()
        
        draw.text((10, 40), "Error:", font=font, fill=0)
        draw.text((10, 60), error[:30], font=font, fill=0)
        
        self.display.display_image(image)
    
    def run_once(self):
        """Update display once and exit"""
        logger.info("=== Running single update ===")
        self.update_display()
    
    def run_continuous(self, interval_minutes=5):
        """Update display continuously"""
        logger.info(f"=== Running continuous mode (update every {interval_minutes}min) ===")
        
        while True:
            try:
                self.update_display()
                
                logger.info(f"Sleeping {interval_minutes} minutes...")
                time.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                logger.info("Interrupted by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                time.sleep(60)  # Wait 1 minute before retry


def main():
    """Entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Bus Display Controller')
    parser.add_argument('--mock-display', action='store_true', help='Use mock display (no hardware)')
    parser.add_argument('--continuous', action='store_true', help='Run continuously')
    parser.add_argument('--interval', type=int, default=5, help='Update interval in minutes (continuous mode)')
    
    args = parser.parse_args()
    
    try:
        display = BusDisplay(mock_display=args.mock_display)
        
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
