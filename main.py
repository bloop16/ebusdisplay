#!/usr/bin/env python3
import time, json, logging
from pathlib import Path
from src.api import VMobilAPI
from src.display.renderer import DisplayRenderer
from src.display.driver import DisplayDriver
from src.power.pisugar import PiSugar

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BusDisplay:
    def __init__(self, config_path='config/stops.json', mock_display=False, mock_battery=False):
        logger.info("Init Bus Display...")
        self.config_path = Path(config_path)
        self.api = VMobilAPI()
        self.renderer = DisplayRenderer()
        self.display = DisplayDriver(mock=mock_display)
        self.pisugar = PiSugar(mock=mock_battery)
        self.stops = []
        self.load_config()
        self.button_pressed = False
        self.pisugar.register_button_callback(lambda: setattr(self, 'button_pressed', True) or self.update_display())
    
    def load_config(self):
        if self.config_path.exists():
            self.stops = json.load(open(self.config_path)).get('stops', [])
    
    def update_display(self):
        if not self.stops: return
        stop = self.stops[0]
        logger.info(f"Update {stop['name']}...")
        try:
            deps = self.api.get_departures(stop_id=stop['id'], limit=4)
            bat = self.pisugar.get_battery_level()
            img = self.renderer.render_departures(deps, stop['name'], battery_percent=bat)
            self.display.display_image(img)
            self.button_pressed = False
        except Exception as e:
            logger.error(f"Fail: {e}")
    
    def run_once(self): self.update_display()
    
    def run_continuous(self, interval=5):
        mode = "auto" if self.pisugar.is_charging() else "button"
        logger.info(f"Mode: {mode}")
        while True:
            try:
                if mode == "auto": self.update_display(); time.sleep(interval * 60)
                elif mode == "button": time.sleep(1) if not self.button_pressed else None
            except KeyboardInterrupt: break
            except: time.sleep(60)

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--mock-display', action='store_true')
    p.add_argument('--mock-battery', action='store_true')
    p.add_argument('--continuous', action='store_true')
    p.add_argument('--interval', type=int, default=5)
    args = p.parse_args()
    d = BusDisplay(mock_display=args.mock_display, mock_battery=args.mock_battery)
    d.run_continuous(args.interval) if args.continuous else d.run_once()
