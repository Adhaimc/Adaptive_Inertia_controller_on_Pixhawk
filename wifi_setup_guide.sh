#!/bin/bash
# Complete WiFi setup guide for Erle-Brain

echo "=========================================="
echo "Erle-Brain WiFi Connection Guide"
echo "=========================================="
echo ""
echo "STEP 1: Connect to Erle-Brain's WiFi"
echo "------------------------------------"
echo "1. Make sure Erle-Brain is powered on and booted (LEDs blinking)"
echo "2. On your Mac, click the WiFi icon in the menu bar"
echo "3. Look for and connect to: erle-robotics-frambuese"
echo "4. The default password is usually: holaerle"
echo ""
echo "Press ENTER when you've connected to the Erle-Brain WiFi..."
read

echo ""
echo "STEP 2: Verify Connection"
echo "------------------------------------"
echo "Checking if we can reach the Erle-Brain..."
if ping -c 3 192.168.7.2 > /dev/null 2>&1; then
    echo "✓ Erle-Brain is reachable at 192.168.7.2"
elif ping -c 3 192.168.8.1 > /dev/null 2>&1; then
    echo "✓ Erle-Brain is reachable at 192.168.8.1"
    ERLE_IP="192.168.8.1"
else
    echo "Trying common Erle-Brain IP addresses..."
    for ip in 10.0.0.1 192.168.1.1 192.168.0.1; do
        if ping -c 2 $ip > /dev/null 2>&1; then
            echo "✓ Erle-Brain found at $ip"
            ERLE_IP="$ip"
            break
        fi
    done
fi

if [ -z "$ERLE_IP" ]; then
    ERLE_IP="192.168.7.2"
fi

echo ""
echo "STEP 3: SSH into Erle-Brain"
echo "------------------------------------"
echo "Attempting to SSH into Erle-Brain at $ERLE_IP..."
echo "Default username: erle"
echo "Default password: erle"
echo ""
echo "After logging in, run these commands to connect to your WiFi:"
echo ""
echo "sudo nmcli device wifi connect \"ZTE_2.4G_Q4pqAG\" password \"YOUR_WIFI_PASSWORD\""
echo ""
echo "Then check the new IP address:"
echo "ifconfig wlan0"
echo ""
echo "Press ENTER to start SSH connection..."
read

ssh erle@$ERLE_IP
