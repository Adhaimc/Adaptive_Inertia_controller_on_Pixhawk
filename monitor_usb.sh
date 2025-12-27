#!/bin/bash
echo "Monitoring for Erle-Brain USB connection..."
echo "Press Ctrl+C to stop"
echo ""

while true; do
    if ifconfig | grep -q "192.168.7"; then
        echo "✓ USB network interface detected!"
        ifconfig | grep -A 5 "192.168.7"
        echo ""
        echo "Attempting to ping Erle-Brain at 192.168.7.2..."
        if ping -c 2 192.168.7.2 > /dev/null 2>&1; then
            echo "✓ Erle-Brain is reachable!"
            echo ""
            echo "You can now SSH with: ssh erle@192.168.7.2"
            break
        else
            echo "✗ Cannot ping 192.168.7.2 yet, waiting..."
        fi
    else
        echo "Waiting for USB connection... (check that Erle-Brain is powered on and connected)"
    fi
    sleep 2
done
