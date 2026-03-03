"""
WiFi Access Point Manager
Creates hotspot for initial setup when no WiFi configured.
"""
import subprocess
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class APManager:
    """Manages WiFi Access Point (hotspot) mode"""
    
    DEFAULT_SSID = "BusDisplay-Setup"
    DEFAULT_PASSWORD = "busdisplay"
    DEFAULT_IP = "192.168.4.1"
    
    def __init__(self, ssid=None, password=None):
        self.ssid = ssid or self.DEFAULT_SSID
        self.password = password or self.DEFAULT_PASSWORD
        self.is_active = False
    
    def is_wifi_configured(self) -> bool:
        """Check if WiFi client mode is configured"""
        wpa_conf = Path("/etc/wpa_supplicant/wpa_supplicant.conf")
        
        if not wpa_conf.exists():
            return False
        
        try:
            content = wpa_conf.read_text()
            # Check for network blocks
            return 'network={' in content
        except:
            return False
    
    def is_wifi_connected(self) -> bool:
        """Check if currently connected to WiFi"""
        try:
            result = subprocess.run(
                ['iwgetid', '-r'],
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.returncode == 0 and result.stdout.strip()
        except:
            return False
    
    def should_start_ap(self) -> bool:
        """Determine if AP mode should be activated
        
        Dual-mode: Start AP if configured AND WiFi is connected
        (allows users to connect via hotspot even when WiFi is active)
        """
        # Always offer AP for configuration/updates
        return True  # Can be overridden with environment variable
    
    def start_ap(self):
        """Start Access Point mode"""
        if self.is_active:
            logger.warning("AP already active")
            return
        
        logger.info(f"Starting AP: {self.ssid}")
        
        try:
            # Create hostapd config
            hostapd_conf = self._create_hostapd_config()
            
            # Create dnsmasq config
            dnsmasq_conf = self._create_dnsmasq_config()
            
            # Configure network interface
            self._configure_interface()
            
            # Start services
            subprocess.run(['sudo', 'systemctl', 'start', 'hostapd'], check=True)
            subprocess.run(['sudo', 'systemctl', 'start', 'dnsmasq'], check=True)
            
            self.is_active = True
            logger.info("AP started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start AP: {e}")
            raise
    
    def stop_ap(self):
        """Stop Access Point mode"""
        if not self.is_active:
            return
        
        logger.info("Stopping AP")
        
        try:
            subprocess.run(['sudo', 'systemctl', 'stop', 'hostapd'], check=False)
            subprocess.run(['sudo', 'systemctl', 'stop', 'dnsmasq'], check=False)
            
            self.is_active = False
            logger.info("AP stopped")
            
        except Exception as e:
            logger.error(f"Failed to stop AP: {e}")
    
    def _create_hostapd_config(self) -> str:
        """Create hostapd configuration"""
        config = f"""
interface=wlan0
driver=nl80211
ssid={self.ssid}
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase={self.password}
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
"""
        
        config_file = Path("/tmp/hostapd.conf")
        config_file.write_text(config.strip())
        
        # Copy to system location (requires sudo)
        subprocess.run([
            'sudo', 'cp', str(config_file), '/etc/hostapd/hostapd.conf'
        ], check=True)
        
        return str(config_file)
    
    def _create_dnsmasq_config(self) -> str:
        """Create dnsmasq configuration"""
        config = f"""
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
domain=wlan
address=/bus-display.local/{self.DEFAULT_IP}
"""
        
        config_file = Path("/tmp/dnsmasq.conf")
        config_file.write_text(config.strip())
        
        subprocess.run([
            'sudo', 'cp', str(config_file), '/etc/dnsmasq.conf'
        ], check=True)
        
        return str(config_file)
    
    def _configure_interface(self):
        """Configure wlan0 for AP mode"""
        commands = [
            ['sudo', 'ip', 'link', 'set', 'wlan0', 'down'],
            ['sudo', 'ip', 'addr', 'flush', 'dev', 'wlan0'],
            ['sudo', 'ip', 'addr', 'add', f'{self.DEFAULT_IP}/24', 'dev', 'wlan0'],
            ['sudo', 'ip', 'link', 'set', 'wlan0', 'up'],
        ]
        
        for cmd in commands:
            subprocess.run(cmd, check=True)
    
    def connect_to_wifi(self, ssid: str, password: str):
        """Connect to WiFi network (client mode)"""
        logger.info(f"Connecting to WiFi: {ssid}")
        
        try:
            # Stop AP if running
            if self.is_active:
                self.stop_ap()
            
            # Add network to wpa_supplicant
            self._add_wifi_network(ssid, password)
            
            # Restart wpa_supplicant
            subprocess.run(['sudo', 'systemctl', 'restart', 'wpa_supplicant'], check=True)
            
            # Wait for connection (simple check)
            import time
            time.sleep(5)
            
            if self.is_wifi_connected():
                logger.info("WiFi connected successfully")
                return True
            else:
                logger.error("WiFi connection failed")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to WiFi: {e}")
            return False
    
    def _add_wifi_network(self, ssid: str, password: str):
        """Add network to wpa_supplicant config"""
        network_block = f"""
network={{
    ssid="{ssid}"
    psk="{password}"
    key_mgmt=WPA-PSK
}}
"""
        
        wpa_conf = Path("/etc/wpa_supplicant/wpa_supplicant.conf")
        
        # Backup existing config
        if wpa_conf.exists():
            subprocess.run([
                'sudo', 'cp', str(wpa_conf), str(wpa_conf) + '.bak'
            ], check=False)
        
        # Append network block
        with open('/tmp/wpa_network.conf', 'w') as f:
            f.write(network_block)
        
        subprocess.run([
            'sudo', 'sh', '-c',
            f'cat /tmp/wpa_network.conf >> {wpa_conf}'
        ], check=True)


def main():
    """Test AP manager"""
    logging.basicConfig(level=logging.INFO)
    
    ap = APManager()
    
    print(f"WiFi configured: {ap.is_wifi_configured()}")
    print(f"WiFi connected: {ap.is_wifi_connected()}")
    print(f"Should start AP: {ap.should_start_ap()}")
    
    if ap.should_start_ap():
        print(f"\nWould start AP: {ap.ssid}")
        print(f"Password: {ap.password}")
        print(f"IP: {ap.DEFAULT_IP}")


if __name__ == '__main__':
    main()
