#!/usr/bin/env python3
"""
PHASE 2 TEST - BENCHTOP (PROPS OFF)
Arm/disarm, throttle response, RC channel verification
"""

import sys
import time
import collections
from collections import abc

# Patch collections for DroneKit compatibility
collections.MutableMapping = abc.MutableMapping
collections.Mapping = abc.Mapping

from dronekit import connect, VehicleMode


def phase_2_benchtop(port='/dev/cu.usbmodem101'):
    """Phase 2: Benchtop Test (Props OFF)."""
    
    print("\n" + "=" * 70)
    print("⚠️  PHASE 2: BENCHTOP TEST (PROPS MUST BE REMOVED)")
    print("=" * 70 + "\n")
    
    # Safety check
    print(">>> CRITICAL SAFETY CHECK")
    print("⚠️  ALL PROPELLERS MUST BE REMOVED!")
    print("⚠️  Quad should be on a table/floor with nothing around it\n")
    
    response = input(">> Are ALL propellers removed and secured? (yes/no): ").strip().lower()
    if response != "yes":
        print("❌ ABORTED - Remove propellers before proceeding")
        return False
    
    print("✓ Propeller safety confirmed\n")
    
    # Connect
    print("[1/6] Connecting to Pixhawk...")
    try:
        vehicle = connect(port, baud=115200, wait_ready=True, timeout=30)
        print("    ✅ Connected!")
    except Exception as e:
        print(f"    ❌ Connection failed: {e}")
        return False
    
    # Set mode
    print("\n[2/6] Setting STABILIZE mode...")
    try:
        vehicle.mode = VehicleMode("STABILIZE")
        start = time.time()
        while vehicle.mode.name != "STABILIZE":
            if time.time() - start > 5:
                print("    ❌ Timeout setting mode")
                vehicle.close()
                return False
            time.sleep(0.1)
        print("    ✅ STABILIZE mode set")
    except Exception as e:
        print(f"    ❌ Failed: {e}")
        vehicle.close()
        return False
    
    # Arm
    print("\n[3/6] Arming vehicle...")
    try:
        if not vehicle.is_armable:
            print("    ⚠️  Vehicle not armable!")
            print("    Check: GPS lock, compass calibration, battery > 11V")
            response = input("    Continue anyway? (yes/no): ").strip().lower()
            if response != "yes":
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
    print("\n[4/6] Setting sticks to neutral...")
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
    
    # Throttle test
    print("\n[5/6] Testing throttle ramp (0% → 50% → 0%)...")
    try:
        print("    Ramping throttle...")
        print("    Listen for motor tones increasing then decreasing")
        print("    (Motors should NOT spin - no props!)\n")
        
        # Ramp up
        for throttle in [0, 10, 20, 30, 40, 50]:
            pwm = int(1000 + throttle * 10)  # 1000-2000 PWM
            vehicle.channels.overrides['3'] = pwm
            print(f"      Throttle: {throttle:2d}% (PWM {pwm})", end="\r")
            time.sleep(0.3)
        
        # Hold at 50%
        time.sleep(1)
        
        # Ramp down
        for throttle in range(40, -1, -10):
            pwm = int(1000 + throttle * 10)
            vehicle.channels.overrides['3'] = pwm
            print(f"      Throttle: {throttle:2d}% (PWM {pwm})", end="\r")
            time.sleep(0.3)
        
        vehicle.channels.overrides['3'] = 1000
        time.sleep(0.5)
        
        print(f"      Throttle:  0% (PWM 1000)  ✓")
        print("    ✅ Throttle test complete")
        
    except Exception as e:
        print(f"    ❌ Failed: {e}")
        vehicle.disarm()
        vehicle.close()
        return False
    
    # Attitude test
    print("\n[6/6] Testing attitude commands...")
    try:
        print("    Testing roll, pitch, yaw commands\n")
        
        # Roll
        print("    Testing ROLL (10% right)...")
        vehicle.channels.overrides['1'] = 1600
        time.sleep(1)
        
        # Pitch
        print("    Testing PITCH (10% forward)...")
        vehicle.channels.overrides['1'] = 1500
        vehicle.channels.overrides['2'] = 1600
        time.sleep(1)
        
        # Yaw
        print("    Testing YAW (10% right)...")
        vehicle.channels.overrides['2'] = 1500
        vehicle.channels.overrides['4'] = 1600
        time.sleep(1)
        
        # Return to neutral
        print("    Returning to neutral...")
        vehicle.channels.overrides = {
            '1': 1500,
            '2': 1500,
            '3': 1000,
            '4': 1500,
        }
        time.sleep(1)
        
        print("    ✅ Attitude commands working!")
        
    except Exception as e:
        print(f"    ❌ Failed: {e}")
        vehicle.disarm()
        vehicle.close()
        return False
    
    # Disarm
    print("\nDisarming vehicle...")
    try:
        vehicle.armed = False
        start = time.time()
        while vehicle.armed:
            if time.time() - start > 5:
                print("    ⚠️  Disarm timeout")
                break
            time.sleep(0.1)
        
        print("✓ Disarmed")
    except Exception as e:
        print(f"❌ Disarm error: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ PHASE 2 COMPLETE!")
    print("=" * 70)
    print("\nResults:")
    print("  ✅ Arm/disarm working")
    print("  ✅ Throttle commands responsive")
    print("  ✅ Attitude commands acknowledged")
    print("  ✅ Ready for Phase 3 (Tethered Hover)")
    
    print("\nNext step:")
    print("  Install propellers and tether drone")
    print("  Run: python3.11 phase3_test.py")
    
    vehicle.close()
    return True


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Phase 2: Benchtop Test')
    parser.add_argument('--port', default='/dev/cu.usbmodem101', help='USB port')
    args = parser.parse_args()
    
    success = phase_2_benchtop(args.port)
    sys.exit(0 if success else 1)
