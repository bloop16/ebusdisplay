# Bus Display - Image Build Guide

Erstelle eine flashbare SD-Card Image wie Pwnagotchi.

## Schneller Weg (Manuell - für Test)

```bash
# 1. Pi OS Lite flashen
#    https://www.raspberrypi.com/software/
#    Schreibe auf SD-Karte

# 2. SSH aktivieren:
#    touch /boot/ssh
#    echo "bus-display" > /etc/hostname

# 3. Auf Pi einloggen und installieren:
ssh pi@bus-display.local

# 4. Repository klonen
cd ~
git clone https://github.com/DEIN_USER/bus-display.git
cd bus-display

# 5. Installation starten
sudo ./install.sh

# 6. Reboot
sudo reboot
```

## Automatisches Image Building (Empfohlen)

```bash
# Voraussetzungen:
# - Ubuntu/Debian Host
# - pi-gen Tool
# - 8GB+ freier Platz

# 1. pi-gen klonen
git clone https://github.com/RPi-Distro/pi-gen

# 2. Bus-Display Stage hinzufügen
cp -r build-tools/bus-display-stage pi-gen/stage5/

# 3. Image bauen (dauert ~2h)
cd pi-gen
./build.sh -c config

# 4. Result: 
#    work/build/latest-armhf.img
#    → Flashe auf SD mit Etcher
```

## Erstes Booten

### Boot-Bildschirm (E-Ink)
- Zeigt: "Bus Display"
- Zeigt: IP-Adresse & Hostname
- Zeigt: WiFi SSID (falls verbunden)

### Web-Interface
- **URL:** `http://bus-display.local:5000` oder `http://<IP>:5000`
- **Tabs:**
  - 🚏 Haltestellen: Konfiguriere Favoriten
  - ⏱️ Live-Abfahrten: Teste Daten
  - 📡 WiFi: Verbinde mit Netzwerk

### Systemd Services
```bash
# Starte Services manuell:
sudo systemctl start bus-display-boot      # Boot-Screen
sudo systemctl start bus-display           # Main Display Loop
sudo systemctl start bus-display-web       # Web-UI

# Status prüfen:
sudo systemctl status bus-display
journalctl -u bus-display -f
```

## Troubleshooting

### "Keine Verbindung zum WebUI"
```bash
# 1. Port prüfen
sudo netstat -tulpn | grep 5000

# 2. Service prüfen
sudo systemctl status bus-display-web

# 3. IP abrufen
hostname -I
```

### "E-Ink zeigt nichts"
```bash
# 1. SPI prüfen
ls -la /dev/spidev*

# 2. GPIO prüfen
gpio readall

# 3. Test im Mock-Modus
python3 main.py --mock-display
```

### "WiFi verbindet sich nicht"
```bash
# 1. WiFi-Scan
sudo iwlist wlan0 scan | grep ESSID

# 2. Logs prüfen
journalctl -u wpa_supplicant -f

# 3. Config prüfen
cat /etc/wpa_supplicant/wpa_supplicant.conf
```

## Nächste Schritte

- [ ] pi-gen Stage erstellen
- [ ] GitHub Actions für automatisches Bauen
- [ ] SD-Image in Releases veröffentlichen
- [ ] Erste Test-Flashe durchführen


