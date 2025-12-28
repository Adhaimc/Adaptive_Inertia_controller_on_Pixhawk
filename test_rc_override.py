#!/usr/bin/env python3
"""
Simple test script for RC Override Controller.
Run this to test basic Pixhawk control without RC receiver.
"""

import sys
import time
from src.rc_override_controller import RCOverrideController, FlightMode


def main():
    """Simple test sequence."""
    
    # Find your USB port: ls /dev/cu.usb*
    PORT = '/dev/cu.usbmodem14101'  # UPDATE THIS WITH YOUR PORT
    
    print("\n" + "=" * 70)
    print("PIXHAWK RC OVERRIDE TEST")
    print("=" * 70)
    
    # Create controller
    controller = RCOverrideController(PORT)
    
    try:
        # Step 1: Connect
        print("\n[1] Connecting to Pixhawk...")
        if not controller.connect():
            print("✗ Connection failed")
            return False
        print("✓ Connected")
        
        # Step 2: Get vehicle info
        print("\n[2] Getting vehicle info...")
        info = controller.get_vehicle_info()
        print(f"  Mode: {info['mode']}")
        print(f"  Armed: {info['armed']}")
        print(f"  Armable: {info['is_armable']}")
        print(f"  Battery: {info['battery']['voltage']:.1f}V")
        print(f"  Attitude: R={info['attitude']['roll']:.1f}° P={info['attitude']['pitch']:.1f}° Y={info['attitude']['yaw']:.1f}°")
        
        # Step 3: Start monitoring
        print("\n[3] Starting vehicle monitoring...")
        controller.start_monitoring()
        time.sleep(1)
        
        # Step 4: Set to STABILIZE mode
        print("\n[4] Setting to STABILIZE mode...")
        if not controller.set_mode(FlightMode.STABILIZE):
            print("✗ Failed to set mode")
            return False
        print("✓ STABILIZE mode set")
        
        # Step 5: Arm
        print("\n[5] Arming vehicle...")
        if not controller.arm():
            print("✗ Failed to arm (check GPS, compass, battery)")
            return False
        print("✓ Armed")
        
        time.sleep(1)
        
        # Step 6: Neutral sticks
        print("\n[6] Setting sticks to neutral...")
        controller.neutral_sticks()
        time.sleep(1)
        
        # Step 7: Test throttle increase
        print("\n[7] Testing throttle (ramping 0% → 50%)...")
        for throttle in range(0, 51, 10):
            print(f"  Throttle: {throttle}%")
            controller.set_throttle(throttle)
            time.sleep(0.5)
        
        # Step 8: Back to neutral
        print("\n[8] Returning to neutral...")
        controller.neutral_sticks()
        time.sleep(1)
        
        # Step 9: Disarm
        print("\n[9] Disarming vehicle...")
        if not controller.disarm():
            print("✗ Failed to disarm")
            return False
        print("✓ Disarmed")
        
        # Step 10: Summary
        print("\n" + "=" * 70)
        print("✓ TEST COMPLETE - ALL CHECKS PASSED")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Review the output above for any warnings")
        print("2. Check battery voltage (should be > 11V for 3S)")
        print("3. Verify attitude readings are stable")
        print("4. Now ready to implement control algorithms!")
        
        return True
    
    except KeyboardInterrupt:
        print("\n\n✗ Test interrupted by user")
        return False
    
    except Exception as e:
        print(f"\n\n✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        print("\nCleaning up...")
        controller.disconnect()


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
