# 🚍 Raspberry Pi Zero Bus Display

## Project Overview
E-Ink bus departure display for Vorarlberg public transport (vmobil.at).

**Hardware:**
- Raspberry Pi Zero W
- PiSugar 2 (Battery HAT with button)
- Waveshare 2.13" e-Paper HAT (250x122px B/W)

## Core Features
1. WiFi setup via captive portal
2. Web interface for stop configuration  
3. Real-time bus departures
4. Smart power management (battery/AC)

## Tech Stack
- Python 3 + Flask
- pytest (TDD)
- BeautifulSoup4 (scraping)
- Waveshare e-Paper library

## Status
- [x] Project init + API research
- [ ] Directory structure
- [ ] Tests + implementation

**Development:** `192.168.0.99:/home/martin/bus-display`
