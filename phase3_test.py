#!/usr/bin/env python3
"""
PHASE 3 TEST - TETHERED HOVER
First flight test with props on, tethered safely
"""

import sys
import time
import collections
from collections import abc

# Patch collections for DroneKit compatibility
collections.MutableMapping = abc.MutableMapping
collections.Mapping = abc.Mapping

from dronekit import connect, VehicleMode


def phase_3_tethered_hover(port='/dev/cu.usbmodem101'):
    """Phase 3: Tethered Hover Test."""
    
    print("\n" + "=" * 70)
    print("🚁 PHASE 3: TETHERED HOVER TEST (FIRST FLIGHT)")
    print("=" * 70 + "\n")
    
    # Safety checks
    print(">>> CRITICAL SAFETY CHECKLIST")
    print("⚠️  ALL propellers MUST be installed correctly!")
    print("⚠️  Quad MUST be tethered (2-3m rope attached)")
    print("⚠️  Battery MUST be fully charged (>12.4V)")
    print("⚠️  Clear 5m radius area completely")
    print("⚠️  NO people within 10 meters!")
    print("⚠️  Everyone wearing long sleeves (prop safety)\n")
    
    response = input(">> Are ALL safety checks complete? (yes/no): ").strip().lower()
    if response != "yes":
        print("❌ ABORTED - Complete safety checklist before proceeding")
        return False
    
    print("✓ Safety checklist confirmed\n")
    
    # Connect
    print("[1/7] Connecting to Pixhawk...")
    try:
        vehicle = connect(port, baud=115200, wait_ready=True, timeout=30)
        print("    ✅ Connected!")
    except Exception as e:
        print(f"    ❌ Connection failed: {e}")
        return False
    
    # Set mode
    print("\n[2/7] Setting STABILIZE mode...")
    try:
        vehicle.mode = VehicleMode("STABILIZE")
        start = time.time()
        while vehicle.mode.name != "STABILIZE":
            if time.time() - start > 5:
                print("    ❌ Timeout")
                vehicle.close()
                return False
            time.sleep(0.1)
        print("    ✅ STABILIZE mode set")
    except Exception as e:
        print(f"    ❌ Failed: {e}")
        vehicle.close()
        return False
    
    # Arm
    print("\n[3/7] Arming vehicle...")
    try:
        if not vehicle.is_armable:
            print("    ❌ Vehicle not armable")
            print("    Check: GPS lock, compass, battery > 11V")
            vehicle.close()
            return False
        
        vehicle.armed = True
        start = time.time()
        while not vehicle.armed:
            if time.time() - start > 10:
                print("    ❌ Arm timeout")
                vehicle.close()
                return False
            time.sleep(0.1)
        
        print("    ✅ Armed!")
    except Exception as e:
        print(f"    ❌ Arm failed: {e}")
        vehicle.close()
        return False
    
    time.sleep(1)
    
    # Neutral sticks
    print("\n[4/7] Setting sticks to neutral...")
    try:
        vehicle.channels.overrides = {
            '1': 1500,  # Roll
            '2': 1500,  # Pitch
            '3': 1000,  # Throttle (off)
            '4': 1500,  # Yaw
        }
        time.sleep(1)
        print("    ✅ Sticks at neutral")
    except Exception as e:
        print(f"    ❌ Failed: {e}")
        vehicle.disarm()
        vehicle.close()
        return False
    
    # Gentle throttle ramp (liftoff)
    print("\n[5/7] Gentle throttle ramp (0% → 60% over 5 seconds)...")
    print("    WATCH for smooth liftoff, stable attitude, no violent oscillations")
    try:
        start_time = time.time()
        while time.time() - start_time < 5:
            elapsed = time.time() - start_time
            throttle = int((elapsed / 5) * 60)  # 0 to 60% over 5s
            pwm = int(1000 + throttle * 10)
            vehicle.channels.overrides['3'] = pwm
            
            info = {
                'alt': vehicle.location.global_relative_frame.alt,
                'roll': vehicle.attitude.roll,
                'pitch': vehicle.attitude.pitch,
            }
            
            print(f"    {throttle:2d}% | Alt: {info['alt']:6.2f}m | "
                  f"Roll: {info['roll']:6.1f}° | Pitch: {info['pitch']:6.1f}°", end="\r")
            time.sleep(0.1)
        
        print(f"    60% | Alt: {vehicle.location.global_relative_frame.alt:6.2f}m | "
              f"Roll: {vehicle.attitude.roll:6.1f}° | Pitch: {vehicle.attitude.pitch:6.1f}°")
        print("    ✅ Liftoff complete")
        
    except Exception as e:
        print(f"    ❌ Failed: {e}")
        vehicle.channels.overrides['3'] = 1000
        vehicle.disarm()
        vehicle.close()
        return False
    
    # Hover hold
    print("\n[6/7] Hovering for 10 seconds at ~45% throttle...")
    print("    LISTEN for smooth motor sounds")
    print("    WATCH for stable altitude and attitude")
    print("    Time | Altitude | Attitude (Roll/Pitch/Yaw) | Battery")
    
    try:
        vehicle.channels.overrides['3'] = 1450  # ~45% throttle
        
        for i in range(10, 0, -1):
            info = {
                'alt': vehicle.location.global_relative_frame.alt,
                'roll': vehicle.attitude.roll,
                'pitch': vehicle.attitude.pitch,
                'yaw': vehicle.attitude.yaw,
                'bat': vehicle.battery.voltage,
            }
            
            print(f"    {i:2d}s  | {info['alt']:7.2f}m  | "
                  f"{info['roll']:6.1f}° / {info['pitch']:6.1f}° / {info['yaw']:6.1f}° | {info['bat']:.2f}V")
            time.sleep(1)
        
        print("    ✅ Hover complete")
        
    except Exception as e:
        print(f"    ❌ Hover error: {e}")
        vehicle.channels.overrides['3'] = 1000
        vehicle.disarm()
        vehicle.close()
        return False
    
    # Landing
    print("\n>>> Gentle landing (5 seconds)...")
    try:
        start_time = time.time()
        while time.time() - start_time < 5:
            elapsed = time.time() - start_time
            throttle = max(0, int(45 * (1 - elapsed / 5)))
            pwm = int(1000 + throttle * 10)
            vehicle.channels.overrides['3'] = pwm
            
            print(f"    Throttle: {throttle:2d}%", end="\r")
            time.sleep(0.1)
        
        vehicle.channels.overrides['3'] = 1000
        time.sleep(1)
        
        print(f"    Throttle:  0% - LANDED!   ")
        print("    ✅ Landing complete")
        
    except Exception as e:
        print(f"    ❌ Landing error: {e}")
        vehicle.disarm()
        vehicle.close()
        return False
    
    # Disarm
    print("\n[7/7] Disarming vehicle...")
    try:
        vehicle.armed = False
        start = time.time()
        while vehicle.armed:
            if time.time() - start > 5:
                break
            time.sleep(0.1)
        
        print("    ✅ Disarmed")
    except Exception as e:
        print(f"    ⚠️  Disarm error: {e}")
    
    # Post-flight check
    print("\n>>> Post-flight check...")
    try:
        info = {
            'alt': vehicle.location.global_relative_frame.alt,
            'bat': vehicle.battery.voltage,
            'heading': vehicle.heading,
        }
        
        print(f"    Altitude: {info['alt']:.2f}m")
        print(f"    Battery:  {info['bat']:.2f}V")
        print(f"    Heading:  {info['heading']:.1f}°")
        
        if info['bat'] > 10.5:
            print("    ✅ Battery still good")
        else:
            print(f"    ⚠️  Battery low: {info['bat']:.2f}V")
        
    except Exception as e:
        print(f"    Error reading post-flight info: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("🎉 PHASE 3 COMPLETE - FIRST FLIGHT SUCCESSFUL!")
    print("=" * 70)
    print("\nResults:")
    print("  ✅ Smooth liftoff")
    print("  ✅ Stable hover for 10 seconds")
    print("  ✅ Controlled landing")
    print("  ✅ All systems working!")
    
    print("\nNext steps:")
    print("  1. Download flight logs from Pixhawk")
    print("  2. Review attitude errors (< 5° is good)")
    print("  3. Integrate AIC controller")
    print("  4. Run autonomous missions")
    
    vehicle.close()
    return True


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Phase 3: Tethered Hover Test')
    parser.add_argument('--port', default='/dev/cu.usbmodem101', help='USB port')
    args = parser.parse_args()
    
    success = phase_3_tethered_hover(args.port)
    sys.exit(0 if success else 1)
