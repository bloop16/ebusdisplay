# 🚀 Installation Guide

## Quick Install (Recommended)

### 1. Flash SD Card
Download image (when available):
```bash
# Download latest release
wget https://github.com/.../bus-display-v1.0.0.img.xz

# Flash with Etcher or dd
sudo dd if=bus-display-v1.0.0.img of=/dev/sdX bs=4M status=progress
```

### 2. Boot & Setup
1. Insert SD card and power on
2. E-Ink shows network info
3. Connect to displayed WiFi
4. Visit `http://<IP-ADDRESS>:5000`
5. Configure bus stops
6. Done! Display updates automatically

---

## Manual Installation

### Prerequisites
- Raspberry Pi Zero W / Zero 2 W
- Waveshare 2.13" e-Paper HAT
- PiSugar 2 (optional)
- Raspberry Pi OS Lite (Bookworm)

### Step 1: Base System
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Clone repository
cd /home/pi
git clone <repo-url> bus-display
cd bus-display
```

### Step 2: Run Installer
```bash
sudo ./install.sh
```

This will:
- Install all dependencies
- Install Waveshare library
- Create systemd services
- Enable auto-start

### Step 3: Reboot
```bash
sudo reboot
```

### Step 4: Configure
1. Display shows setup instructions
2. Note the IP address
3. Visit web interface: `http://<IP>:5000`
4. Search and add bus stops
5. Save configuration

Display updates automatically every 5 minutes!

---

## Service Management

### Check Status
```bash
# Main controller
sudo systemctl status bus-display

# Web interface
sudo systemctl status bus-display-web

# Boot screen
sudo systemctl status bus-display-boot
```

### View Logs
```bash
# Real-time logs
journalctl -u bus-display -f

# Web interface logs
journalctl -u bus-display-web -f
```

### Manual Control
```bash
# Stop/start services
sudo systemctl stop bus-display
sudo systemctl start bus-display

# Restart
sudo systemctl restart bus-display

# Disable auto-start
sudo systemctl disable bus-display
```

---

## Manual Testing (Without Services)

```bash
cd /home/pi/bus-display

# Test display (mock mode)
python3 main.py --mock-display

# Test web interface
python3 -m src.web.app
# Visit: http://<IP>:5000

# Single update
sudo python3 main.py

# Continuous updates
sudo python3 main.py --continuous --interval 5
```

---

## Troubleshooting

### Display Not Working
```bash
# Check if e-Paper HAT is detected
ls /dev/spidev0.0

# Check Waveshare library
python3 -c "from waveshare_epd import epd2in13_V4; print('OK')"

# Run in mock mode
python3 main.py --mock-display
```

### Web Interface Not Accessible
```bash
# Check if service is running
sudo systemctl status bus-display-web

# Check port
sudo netstat -tulpn | grep :5000

# Test locally
curl http://localhost:5000
```

### No Bus Departures
```bash
# Check configuration
cat config/stops.json

# Check logs
journalctl -u bus-display -n 50

# Test API manually
python3 -c "from src.api import VMobilAPI; api = VMobilAPI(); print(api.search_stops('Bregenz'))"
```

### Network Issues
```bash
# Check WiFi
iwconfig

# Check IP
ip addr

# Test connectivity
ping -c 3 vmobil.at
```

---

## Configuration Files

### Bus Stops
Location: `/home/pi/bus-display/config/stops.json`

Example:
```json
{
  "stops": [
    {"id": "1", "name": "Bregenz Bahnhof"},
    {"id": "2", "name": "Bregenz Hafen"}
  ]
}
```

### WiFi (optional)
Location: `/boot/wpa_supplicant.conf`

---

## Updating

```bash
cd /home/pi/bus-display
git pull
sudo systemctl restart bus-display
```

---

## Uninstall

```bash
# Stop and disable services
sudo systemctl stop bus-display bus-display-web bus-display-boot
sudo systemctl disable bus-display bus-display-web bus-display-boot

# Remove services
sudo rm /etc/systemd/system/bus-display*.service
sudo systemctl daemon-reload

# Remove files
rm -rf /home/pi/bus-display
```

---

## Support

- Issues: GitHub Issues
- Logs: `journalctl -u bus-display`
- Test mode: `python3 main.py --mock-display`
