#!/bin/bash
# Commands to run on Erle-Brain to connect to your WiFi

echo "=========================================="
echo "Erle-Brain WiFi Configuration Commands"
echo "=========================================="
echo ""
echo "Run these commands on the Erle-Brain (after SSH):"
echo ""
echo "1. Create WiFi configuration file:"
echo "-----------------------------------"
echo ""
cat << 'EOF'
sudo su
wpa_passphrase "ZTE_2.4G_Q4pqAG" "YOUR_WIFI_PASSWORD" >> /etc/wpa_supplicant/wpa_supplicant.conf
EOF
echo ""
echo "2. Restart the wireless interface:"
echo "-----------------------------------"
echo ""
cat << 'EOF'
sudo ifdown wlan0
sudo ifup wlan0
EOF
echo ""
echo "OR restart the network service:"
echo ""
cat << 'EOF'
sudo systemctl restart networking
EOF
echo ""
echo "3. Check the new IP address:"
echo "-----------------------------------"
echo ""
cat << 'EOF'
ifconfig wlan0
EOF
echo ""
echo "OR:"
echo ""
cat << 'EOF'
ip addr show wlan0
EOF
echo ""
echo "4. Find your Erle-Brain's new IP:"
echo "-----------------------------------"
echo "Look for 'inet' followed by an IP address (e.g., 192.168.1.XXX)"
echo ""
echo "5. Test from your Mac:"
echo "-----------------------------------"
echo "ssh erle@<NEW_IP_ADDRESS>"
echo ""
