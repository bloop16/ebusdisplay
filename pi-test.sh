#!/bin/bash
# Bus Display - Quick Test Script für USB-Pi
# Verwende diesen Script um Bus-Display auf echtem Pi zu testen

set -e

echo "=========================================="
echo "🚍 Bus Display - Pi Quick Test"
echo "=========================================="
echo ""

# Schritt 1: Repository prüfen
if [ ! -d "bus-display" ]; then
    echo "❌ Repo nicht gefunden!"
    echo "Nutze: git clone <REPO> bus-display"
    exit 1
fi

cd bus-display

echo "✓ Repository gefunden"

# Schritt 2: Config prüfen
if [ ! -f "config/stops.json" ]; then
    echo "⚠️  Config nicht vorhanden, erstelle Default..."
    mkdir -p config
    cat > config/stops.json << 'EOF'
{
  "stops": [
    {
      "id": "490085500",
      "name": "Bregenz Bahnhof"
    }
  ]
}
EOF
fi

echo "✓ Config vorhanden"

# Schritt 3: Abhängigkeiten prüfen
echo ""
echo "Prüfe Python-Abhängigkeiten..."
python3 -c "from src.api import VMobilAPI; print('✓ VMobil API importierbar')" || exit 1
python3 -c "from src.display.renderer import DisplayRenderer; print('✓ Display Renderer OK')" || exit 1

# Schritt 4: Web-Interface testen
echo ""
echo "Starte Web-Interface (STRG+C zum beenden)..."
echo "URL: http://192.168.1.XXX:5000 (IP anpassen)"
echo ""
echo "Available Tests:"
echo "  🚏 Haltestellen: http://<IP>:5000 → Tab 'Haltestellen'"
echo "  ⏱️  Live-Abfahrten: http://<IP>:5000 → Tab 'Live-Abfahrten'"
echo "  📡 WiFi: http://<IP>:5000 → Tab 'WiFi'"
echo ""

python3 -m src.web.app

