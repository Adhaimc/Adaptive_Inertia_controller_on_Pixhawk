#!/bin/bash
# Script to connect to Erle-Brain via USB adapter

ERLE_IP="192.168.7.2"
ERLE_USER="erle"
ERLE_PASS="erle"

# Check for USB network interface
if ifconfig | grep -q "192.168.7.1"; then
    echo "USB network interface detected."
else
    echo "USB network interface not found. Please check your connection."
    exit 1
fi

# Ping Erle-Brain
ping -c 3 $ERLE_IP > /dev/null
if [ $? -eq 0 ]; then
    echo "Erle-Brain is reachable at $ERLE_IP."
else
    echo "Cannot reach Erle-Brain at $ERLE_IP. Check USB connection and power."
    exit 1
fi

# SSH into Erle-Brain
ssh $ERLE_USER@$ERLE_IP
