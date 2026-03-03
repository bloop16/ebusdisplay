# 🚍 Raspberry Pi Zero Bus Display

E-Ink display showing real-time bus departures for Vorarlberg public transport (vmobil.at).

## Hardware
- Raspberry Pi Zero W
- PiSugar 2 Battery HAT
- Waveshare 2.13" e-Paper HAT (250x122px)

## Features
- WiFi setup via captive portal
- Web interface for bus stop configuration
- Real-time departure display
- Smart power management (battery/AC modes)

## Development
```bash
# Install dependencies
pip3 install -r requirements.txt

# Run tests
pytest tests/

# Start web interface
python3 -m src.web.app
```

## TDD Approach
All features require tests FIRST, then implementation.

---
**Development:** 192.168.0.99:/home/martin/bus-display
