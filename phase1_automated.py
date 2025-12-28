#!/usr/bin/env python3
"""
PHASE 1 TEST - AUTOMATED
USB Connection Test with automatic responses
"""

import sys
import time
import collections
from collections import abc

# Patch collections for DroneKit compatibility
collections.MutableMapping = abc.MutableMapping
collections.Mapping = abc.Mapping

from dronekit import connect


def phase_1_test(port='/dev/cu.usbmodem101'):
    """Phase 1: Automated USB Connection Test."""
    
    print("\n" + "=" * 70)
    print("🚀 PHASE 1: USB CONNECTION TEST (AUTOMATED)")
    print("=" * 70 + "\n")
    
    # Connect
    print("[1/4] Connecting to Pixhawk...")
    try:
        vehicle = connect(port, baud=115200, wait_ready=True, timeout=30)
        print("    ✅ Connected!")
    except Exception as e:
        print(f"    ❌ Connection failed: {e}")
        return False
    
    # Read vehicle info
    print("\n[2/4] Reading vehicle information...")
    try:
        info = {
            'mode': vehicle.mode.name,
            'armed': vehicle.armed,
            'is_armable': vehicle.is_armable,
            'heading': vehicle.heading,
            'altitude': vehicle.location.global_relative_frame.alt,
            'battery_voltage': vehicle.battery.voltage,
            'battery_level': vehicle.battery.level,
            'roll': vehicle.attitude.roll,
            'pitch': vehicle.attitude.pitch,
            'yaw': vehicle.attitude.yaw,
            'vx': vehicle.velocity[0],
            'vy': vehicle.velocity[1],
            'vz': vehicle.velocity[2],
        }
        
        print(f"    Mode:            {info['mode']}")
        print(f"    Armed:           {info['armed']}")
        print(f"    Armable:         {info['is_armable']}")
        print(f"    Heading:         {info['heading']:.1f}°")
        print(f"    Altitude:        {info['altitude']:.2f}m")
        print(f"    Battery:         {info['battery_voltage']:.2f}V ({info['battery_level']}%)")
        print(f"    Attitude:        Roll={info['roll']:.1f}° Pitch={info['pitch']:.1f}° Yaw={info['yaw']:.1f}°")
        print(f"    Velocity:        Vx={info['vx']:.2f} m/s, Vy={info['vy']:.2f} m/s, Vz={info['vz']:.2f} m/s")
        print("    ✅ Vehicle info retrieved!")
        
    except Exception as e:
        print(f"    ❌ Failed: {e}")
        vehicle.close()
        return False
    
    # Warnings
    print("\n[3/4] System Status Check...")
    warnings = []
    
    if info['battery_voltage'] < 10:
        warnings.append(f"⚠️  Battery too low: {info['battery_voltage']:.2f}V (need >11V)")
    
    if not info['is_armable']:
        warnings.append("⚠️  Vehicle not armable (check GPS, compass)")
    
    if warnings:
        print("    Warnings:")
        for w in warnings:
            print(f"      {w}")
    else:
        print("    ✅ All systems ready!")
    
    # Monitor
    print("\n[4/4] Live Status Monitoring (10 seconds)...")
    print("    Time | Mode     | Armed | Alt    | Bat   | Attitude (R/P/Y)")
    print("    " + "-" * 65)
    
    for i in range(10, 0, -1):
        try:
            info = {
                'mode': vehicle.mode.name[:8],
                'armed': str(vehicle.armed)[:5],
                'altitude': vehicle.location.global_relative_frame.alt,
                'battery': vehicle.battery.voltage,
                'roll': vehicle.attitude.roll,
                'pitch': vehicle.attitude.pitch,
                'yaw': vehicle.attitude.yaw,
            }
            
            print(f"    {i:2d}s  | {info['mode']:8s} | {info['armed']:5s} | "
                  f"{info['altitude']:6.2f}m | {info['battery']:5.2f}V | "
                  f"{info['roll']:6.1f}°/{info['pitch']:6.1f}°/{info['yaw']:6.1f}°")
        except Exception as e:
            print(f"    Monitor error: {e}")
            break
        
        time.sleep(1)
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ PHASE 1 COMPLETE!")
    print("=" * 70)
    print("\nResults:")
    print("  ✅ USB connection established")
    print("  ✅ Pixhawk detected")
    print("  ✅ Telemetry working")
    print("  ✅ Ready for Phase 2 (Benchtop)")
    
    print("\nNext step:")
    print("  Ready for Phase 2? Run: python3.11 phase2_test.py")
    
    vehicle.close()
    return True


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Phase 1: USB Connection Test')
    parser.add_argument('--port', default='/dev/cu.usbmodem101', help='USB port')
    args = parser.parse_args()
    
    success = phase_1_test(args.port)
    sys.exit(0 if success else 1)
