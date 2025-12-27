#!/bin/bash
# Helper script to find and connect to Erle-Brain 2

echo "=========================================="
echo "Erle-Brain 2 Connection Helper"
echo "=========================================="
echo ""

# Get current network
echo "Your current network:"
ifconfig | grep "inet " | grep -v 127.0.0.1
echo ""

# Try common Erle-Brain hostnames
echo "Trying common hostnames..."
for hostname in erle-brain-2.local erle-brain.local erlerobot.local; do
    echo -n "Trying $hostname... "
    if ping -c 1 -W 2 $hostname &>/dev/null; then
        echo "✓ Found!"
        echo ""
        echo "Try connecting with:"
        echo "  ssh erle@$hostname"
        echo "  Password: holaerle"
        exit 0
    else
        echo "✗"
    fi
done

echo ""
echo "Hostnames not found. Scanning network..."
echo "(This may take a moment...)"
echo ""

# Get network range
NETWORK=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)
if [ -z "$NETWORK" ]; then
    echo "❌ Could not determine network"
    exit 1
fi

SUBNET=$(echo $NETWORK | cut -d. -f1-3)

echo "Scanning ${SUBNET}.0/24 for SSH devices..."
echo ""

# Scan for devices with SSH open (port 22)
for i in {1..254}; do
    IP="${SUBNET}.${i}"
    # Quick check if host is up and has SSH
    timeout 0.2 bash -c "echo >/dev/tcp/${IP}/22" 2>/dev/null && echo "Found SSH at: $IP"
done

echo ""
echo "=========================================="
echo ""
echo "If you found an IP address above, try:"
echo "  ssh erle@<IP_ADDRESS>"
echo "  Password: holaerle"
echo ""
echo "Alternative: Check if Erle-Brain is creating its own WiFi network"
echo "  - Look for 'erle-brain' or 'erlerobot' SSID"
echo "  - Connect to it, then try: ssh erle@192.168.7.2"
echo ""
echo "Make sure:"
echo "  □ Erle-Brain 2 is powered on"
echo "  □ It's connected to the same WiFi network"
echo "  □ SSH is enabled on Erle-Brain"
echo ""
