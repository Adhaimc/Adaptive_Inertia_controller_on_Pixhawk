#!/bin/bash
# Connect to Erle-Brain after joining its WiFi network

echo "=========================================="
echo "Erle-Brain Connection - erle-robotics-frambuese"
echo "=========================================="
echo ""
echo "Make sure you're connected to WiFi: erle-robotics-frambuese"
echo ""
echo "Testing common Erle-Brain IP addresses..."
echo ""

# Try common Erle-Brain IPs
for IP in 11.0.0.1 192.168.7.2 10.0.0.1 192.168.1.1; do
    echo -n "Trying $IP... "
    if ping -c 1 -W 2 $IP &>/dev/null; then
        echo "✓ Responds!"
        echo ""
        echo "=========================================="
        echo "SUCCESS! Erle-Brain found at: $IP"
        echo "=========================================="
        echo ""
        echo "Connect with:"
        echo "  ssh erle@$IP"
        echo "  Password: holaerle"
        echo ""
        echo "Press Enter to connect now, or Ctrl+C to cancel..."
        read
        ssh erle@$IP
        exit 0
    else
        echo "✗ No response"
    fi
done

echo ""
echo "=========================================="
echo "Could not find Erle-Brain automatically"
echo "=========================================="
echo ""
echo "Manual steps:"
echo "1. Make sure you're connected to: erle-robotics-frambuese"
echo "2. Check your IP address: ifconfig | grep 'inet '"
echo "3. The gateway IP should be the Erle-Brain"
echo "4. Try: ssh erle@<gateway_ip>"
echo "   Password: holaerle"
echo ""
