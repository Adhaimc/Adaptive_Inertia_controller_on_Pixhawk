#!/bin/bash
# Monitor for Erle-Brain USB connection

echo "=========================================="
echo "Erle-Brain USB Connection Monitor"
echo "=========================================="
echo ""
echo "Current serial devices:"
ls /dev/tty.* 2>/dev/null
echo ""
echo "----------------------------------------"
echo ""
echo "Waiting for Erle-Brain USB connection..."
echo "(Connect USB cable now if not already connected)"
echo ""
echo "Watching for new devices... (Press Ctrl+C to stop)"
echo ""

# Store initial devices
INITIAL_DEVICES=$(ls /dev/tty.* 2>/dev/null)

# Watch for changes
while true; do
    CURRENT_DEVICES=$(ls /dev/tty.* 2>/dev/null)
    
    # Check for new devices
    NEW_DEVICES=$(comm -13 <(echo "$INITIAL_DEVICES") <(echo "$CURRENT_DEVICES"))
    
    if [ ! -z "$NEW_DEVICES" ]; then
        echo ""
        echo "✓ NEW DEVICE DETECTED!"
        echo "=========================================="
        echo "$NEW_DEVICES"
        echo "=========================================="
        echo ""
        
        # Check if it looks like Erle-Brain
        for device in $NEW_DEVICES; do
            echo "Trying to connect via SSH over USB..."
            echo ""
            echo "Common USB IPs for Erle-Brain:"
            echo "  1. ssh erle@192.168.7.2"
            echo "  2. ssh erle@192.168.6.2"
            echo ""
            echo "Testing 192.168.7.2..."
            
            if ping -c 1 -W 2 192.168.7.2 &>/dev/null; then
                echo "✓ Found Erle-Brain at 192.168.7.2!"
                echo ""
                echo "Connect with: ssh erle@192.168.7.2"
                echo "Password: holaerle"
                exit 0
            fi
            
            echo "Testing 192.168.6.2..."
            if ping -c 1 -W 2 192.168.6.2 &>/dev/null; then
                echo "✓ Found Erle-Brain at 192.168.6.2!"
                echo ""
                echo "Connect with: ssh erle@192.168.6.2"
                echo "Password: holaerle"
                exit 0
            fi
        done
        
        echo ""
        echo "USB device detected but SSH not responding yet."
        echo "Wait a moment for Erle-Brain to boot, then try:"
        echo "  ssh erle@192.168.7.2"
        echo "  Password: holaerle"
        exit 0
    fi
    
    sleep 1
done
