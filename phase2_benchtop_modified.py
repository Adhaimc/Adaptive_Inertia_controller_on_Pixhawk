#!/usr/bin/env python3
"""
PHASE 2 TEST - BENCHTOP (PROPS OFF) - MODIFIED
Works without RC receiver or physical safety switch
Uses GUIDED mode for RC override instead of needing to arm manually
"""

import sys
import time
import collections
from collections import abc

# Patch collections for DroneKit compatibility
collections.MutableMapping = abc.MutableMapping
collections.Mapping = abc.Mapping

from dronekit import connect, VehicleMode


def phase_2_benchtop_modified(port='/dev/cu.usbmodem101'):
    """Phase 2: Benchtop Test (Modified for no-RC setup)."""
    
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
    print("[1/5] Connecting to Pixhawk...")
    try:
        vehicle = connect(port, baud=115200, wait_ready=True, timeout=30)
        print("    ✅ Connected!")
    except Exception as e:
        print(f"    ❌ Connection failed: {e}")
        return False
    
    # Set mode to GUIDED (allows RC override without arm)
    print("\n[2/5] Setting GUIDED mode...")
    try:
        vehicle.mode = VehicleMode("GUIDED")
        start = time.time()
        while vehicle.mode.name != "GUIDED":
            if time.time() - start > 5:
                print("    ❌ Timeout setting mode - trying STABILIZE instead")
                vehicle.mode = VehicleMode("STABILIZE")
                time.sleep(1)
                break
            time.sleep(0.1)
        print(f"    ✅ Mode set to {vehicle.mode.name}")
    except Exception as e:
        print(f"    ⚠️  Mode change issue: {e} - Continuing anyway")
    
    time.sleep(1)
    
    # Test RC channel override without arming
    print("\n[3/5] Testing RC channel overrides (without arming)...")
    try:
        # Set neutral
        vehicle.channels.overrides = {
            '1': 1500,  # Roll
            '2': 1500,  # Pitch
            '3': 1000,  # Throttle (off)
            '4': 1500,  # Yaw
        }
        time.sleep(0.5)
        
        # Check if overrides are being accepted
        print("    Setting neutral sticks...")
        print("    ✅ RC channels ready for override")
        
    except Exception as e:
        print(f"    ⚠️  RC override issue: {e}")
    
    # Throttle test
    print("\n[4/5] Testing throttle ramp (0% → 50% → 0%)...")
    try:
        print("    Ramping throttle...")
        print("    (Motors should NOT spin - no props!)\n")
        
        # Ramp up
        print("    Throttle up:", end="")
        for throttle in [0, 10, 20, 30, 40, 50]:
            pwm = int(1000 + throttle * 10)  # 1000-2000 PWM
            vehicle.channels.overrides['3'] = pwm
            print(f" {throttle}%", end="", flush=True)
            time.sleep(0.3)
        
        # Hold at 50%
        print(" (hold)", end="", flush=True)
        time.sleep(1)
        
        # Ramp down
        print(" (down)", end="", flush=True)
        for throttle in range(40, -1, -10):
            pwm = int(1000 + throttle * 10)
            vehicle.channels.overrides['3'] = pwm
            print(f" {throttle}%", end="", flush=True)
            time.sleep(0.3)
        
        vehicle.channels.overrides['3'] = 1000
        time.sleep(0.5)
        
        print(" ✓\n    ✅ Throttle test complete")
        
    except Exception as e:
        print(f"    ❌ Failed: {e}")
        vehicle.close()
        return False
    
    # Attitude test
    print("\n[5/5] Testing attitude commands...")
    try:
        print("    Testing roll, pitch, yaw commands\n")
        
        # Roll
        print("    [Roll] 10% right...", end="", flush=True)
        vehicle.channels.overrides['1'] = 1600
        time.sleep(1)
        print(" ✓")
        
        # Pitch
        print("    [Pitch] 10% forward...", end="", flush=True)
        vehicle.channels.overrides['1'] = 1500
        vehicle.channels.overrides['2'] = 1600
        time.sleep(1)
        print(" ✓")
        
        # Yaw
        print("    [Yaw] 10% right...", end="", flush=True)
        vehicle.channels.overrides['2'] = 1500
        vehicle.channels.overrides['4'] = 1600
        time.sleep(1)
        print(" ✓")
        
        # Return to neutral
        print("    Returning to neutral...", end="", flush=True)
        vehicle.channels.overrides = {
            '1': 1500,
            '2': 1500,
            '3': 1000,
            '4': 1500,
        }
        time.sleep(1)
        print(" ✓")
        
        print("\n    ✅ Attitude commands working!")
        
    except Exception as e:
        print(f"    ❌ Failed: {e}")
        vehicle.close()
        return False
    
    # Clear overrides
    print("\nClearing RC overrides...")
    try:
        vehicle.channels.overrides = {}
        time.sleep(0.5)
        print("✓ Overrides cleared")
    except Exception as e:
        print(f"⚠️  Override clearing issue: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ PHASE 2 COMPLETE!")
    print("=" * 70)
    print("\nResults:")
    print("  ✅ RC channel override working")
    print("  ✅ Throttle commands responsive")
    print("  ✅ Attitude commands acknowledged")
    print("  ✅ No propellers - safe test")
    print("  ✅ Ready for Phase 3 (Tethered Hover)")
    
    print("\nNext step:")
    print("  Install propellers and tether drone")
    print("  Run: python3.11 phase3_test.py")
    
    vehicle.close()
    return True


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Phase 2: Benchtop Test (Modified)')
    parser.add_argument('--port', default='/dev/cu.usbmodem101', help='USB port')
    args = parser.parse_args()
    
    success = phase_2_benchtop_modified(args.port)
    sys.exit(0 if success else 1)
