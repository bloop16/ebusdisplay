#!/bin/bash
# Bus Display – Installation für Raspberry Pi Zero
# Waveshare 2.13" e-Paper HAT V4 + PiSugar 3
# Ausführen als root: sudo ./install.sh

set -e
echo "=== Bus Display Installation ==="

if [ "$EUID" -ne 0 ]; then
    echo "FEHLER: Als root ausführen (sudo ./install.sh)"
    exit 1
fi

ACTUAL_USER=${SUDO_USER:-pi}
INSTALL_DIR="/home/${ACTUAL_USER}/bus-display"

echo "Benutzer: $ACTUAL_USER"
echo "Verzeichnis: $INSTALL_DIR"

# ── System-Pakete ─────────────────────────────────────────────
apt-get update
apt-get install -y \
    python3 python3-pip \
    python3-pil \
    python3-rpi.gpio \
    python3-spidev \
    git curl

# ── SPI aktivieren (Waveshare Display) ───────────────────────
echo "SPI aktivieren..."
raspi-config nonint do_spi 0

# ── I2C aktivieren (PiSugar 3) ────────────────────────────────
echo "I2C aktivieren..."
raspi-config nonint do_i2c 0

# ── Waveshare e-Paper Bibliothek ──────────────────────────────
echo "Waveshare Bibliothek installieren..."
cd /tmp
rm -rf e-Paper
git clone --depth=1 https://github.com/waveshare/e-Paper.git
pip3 install ./e-Paper/RaspberryPi_JetsonNano/python/ \
    --break-system-packages 2>/dev/null || \
    pip3 install ./e-Paper/RaspberryPi_JetsonNano/python/
rm -rf /tmp/e-Paper

# ── pip Dependencies ──────────────────────────────────────────
cd "$INSTALL_DIR"
pip3 install -r requirements.txt \
    --break-system-packages 2>/dev/null || \
    pip3 install -r requirements.txt

# ── PiSugar 3 Daemon ──────────────────────────────────────────
echo "PiSugar 3 installieren..."
curl -s https://cdn.pisugar.com/release/pisugar-power-manager.sh | bash

# ── Systemd Service ───────────────────────────────────────────
echo "Service einrichten..."
cp "$INSTALL_DIR/systemd/bus-display.service" /etc/systemd/system/
sed -i "s|/home/pi/bus-display|$INSTALL_DIR|g" /etc/systemd/system/bus-display.service
sed -i "s|User=pi|User=$ACTUAL_USER|g"          /etc/systemd/system/bus-display.service

systemctl daemon-reload
systemctl enable bus-display
systemctl start bus-display

echo ""
echo "=== Fertig! ==="
echo "Log: journalctl -u bus-display -f"
