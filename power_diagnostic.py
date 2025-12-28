#!/usr/bin/env python3
"""
POWER DIAGNOSTIC - Check battery and power module status
Helps identify battery or power connection issues
"""

import sys
import time
import collections
from collections import abc

# Patch collections for DroneKit compatibility
collections.MutableMapping = abc.MutableMapping
collections.Mapping = abc.Mapping

from dronekit import connect


def check_power_status(port='/dev/cu.usbmodem101'):
    """Diagnose power issues."""
    
    print("\n" + "=" * 70)
    print("🔋 POWER & BATTERY DIAGNOSTIC")
    print("=" * 70 + "\n")
    
    # Connect
    print("[1/4] Connecting to Pixhawk...")
    try:
        vehicle = connect(port, baud=115200, wait_ready=True, timeout=30)
        print("    ✅ Connected\n")
    except Exception as e:
        print(f"    ❌ Connection failed: {e}")
        return False
    
    # Check battery
    print("[2/4] Checking Battery Status...")
    try:
        battery = vehicle.battery
        print(f"    Voltage:        {battery.voltage:.2f}V")
        print(f"    Current:        {battery.current:.2f}A")
        print(f"    Level:          {battery.level}%")
        print()
        
        if battery.voltage == 0:
            print("    ❌ PROBLEM: Battery voltage is 0V!")
            print("    This means the power module is not connected or not powered.")
        elif battery.voltage < 9:
            print("    ❌ PROBLEM: Battery voltage too low (<9V)!")
            print("    Battery is severely depleted or not connected.")
        elif battery.voltage < 11:
            print("    ⚠️  WARNING: Battery voltage low (<11V)")
            print("    Battery needs charging (target >12.4V for 3S)")
        else:
            print("    ✅ Battery voltage OK")
        
    except Exception as e:
        print(f"    ❌ Failed to read battery: {e}")
        vehicle.close()
        return False
    
    # Check power state
    print("\n[3/4] Checking Power State...")
    try:
        print(f"    System Voltage:  {vehicle.system_status.state}")
        print(f"    Autopilot:       {vehicle.autopilot}")
        
        # Check if we're getting any power
        if vehicle.battery.voltage > 0:
            print("    ✅ Pixhawk is powered")
        else:
            print("    ❌ Pixhawk shows no power input")
        
    except Exception as e:
        print(f"    ⚠️  Status check issue: {e}")
    
    # Recommendations
    print("\n[4/4] Diagnostic Recommendations...\n")
    
    battery_voltage = vehicle.battery.voltage
    
    if battery_voltage == 0:
        print("    🔴 CRITICAL ISSUES TO CHECK:")
        print("       1. Is the battery CONNECTED to the power module?")
        print("          → Check XT60/XT90 connector is fully plugged in")
        print("          → Look for corrosion or damaged connectors")
        print()
        print("       2. Is the power module CONNECTED to the Pixhawk?")
        print("          → Check the 6-pin connector (red/black wires)")
        print("          → Ensure it's fully seated")
        print("          → Try disconnecting and reconnecting")
        print()
        print("       3. Is the battery CHARGED?")
        print("          → Use a multimeter to check battery voltage directly")
        print("          → Expected: 12.6V for fully charged 3S LiPo")
        print("          → Minimum for operation: 11V")
        print()
        print("    📋 NEXT STEPS:")
        print("       1. Disconnect USB from Pixhawk")
        print("       2. Use multimeter to check:")
        print("          - Battery voltage (measure directly at XT60)")
        print("          - Power module input (at battery connector)")
        print("          - Power module output (at Pixhawk connector)")
        print("       3. Reseat all connectors firmly")
        print("       4. Rerun this diagnostic")
        
    elif battery_voltage < 11:
        print("    🟡 BATTERY NEEDS CHARGING:")
        print(f"       Current voltage: {battery_voltage:.2f}V")
        print("       Minimum needed:  11.0V")
        print("       Optimal for ops: 12.4V+")
        print()
        print("    📋 CHARGE YOUR BATTERY:")
        print("       1. Disconnect from Pixhawk")
        print("       2. Use LiPo charger (3S setting)")
        print("       3. Charge to 12.6V (full)")
        print("       4. Come back and retest")
        
    else:
        print("    ✅ POWER SYSTEM LOOKS GOOD!")
        print(f"       Battery voltage: {battery_voltage:.2f}V")
        print("       You can proceed with testing")
        print()
        print("    If motors still not spinning:")
        print("       1. Check motor/ESC connections")
        print("       2. Verify propeller directions in Phase 3")
        print("       3. Check ESC calibration")
    
    print("\n" + "=" * 70)
    
    vehicle.close()
    return battery_voltage > 0


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Power & Battery Diagnostic')
    parser.add_argument('--port', default='/dev/cu.usbmodem101', help='USB port')
    args = parser.parse_args()
    
    success = check_power_status(args.port)
    sys.exit(0 if success else 1)
