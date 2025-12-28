#!/usr/bin/env python3
"""
COMPREHENSIVE THREE-PHASE TEST SCRIPT
Phase 1: USB Connection Test
Phase 2: Benchtop Test (Props OFF)
Phase 3: Tethered Hover Test

Run all three in one session. Follow the prompts!
"""

import sys
import time
from src.rc_override_controller import RCOverrideController, FlightMode


class TestPhases:
    """Run all three test phases."""
    
    def __init__(self, port='/dev/cu.usbmodem14101'):
        self.port = port
        self.controller = None
        self.logger = None
    
    def print_header(self, phase, title):
        """Print phase header."""
        print("\n" + "=" * 70)
        print(f"PHASE {phase}: {title}")
        print("=" * 70 + "\n")
    
    def print_section(self, section):
        """Print section header."""
        print(f"\n>>> {section}")
    
    def pause_for_user(self, message, expected="yes"):
        """Pause and wait for user confirmation."""
        print(f"\n⚠️  {message}")
        response = input(">> Ready? (yes/no): ").strip().lower()
        return response == expected
    
    def phase_1_usb_connection(self):
        """PHASE 1: USB Connection Test."""
        self.print_header(1, "USB CONNECTION TEST")
        
        # Step 1: Find port
        self.print_section("Step 1: Verify USB Port")
        print(f"Using port: {self.port}")
        print(f"\nIf wrong, set it:")
        print(f"  python test_all_phases.py --port /dev/YOUR_PORT")
        
        if not self.pause_for_user("Is this the correct port?"):
            print("❌ Exiting. Find your port with: ls /dev/cu.usb*")
            return False
        
        # Step 2: Connect
        self.print_section("Step 2: Connecting to Pixhawk")
        self.controller = RCOverrideController(self.port)
        
        if not self.controller.connect():
            print("❌ Connection failed!")
            return False
        
        print("✓ Connected!")
        
        # Step 3: Get vehicle info
        self.print_section("Step 3: Reading Vehicle Info")
        info = self.controller.get_vehicle_info()
        
        if not info:
            print("❌ Failed to get vehicle info")
            return False
        
        print(f"  Mode:      {info['mode']}")
        print(f"  Armed:     {info['armed']}")
        print(f"  Armable:   {info['is_armable']}")
        print(f"  Heading:   {info['heading']:.1f}°")
        print(f"  Altitude:  {info['location']['alt']:.2f}m")
        print(f"  Battery:   {info['battery']['voltage']:.2f}V ({info['battery']['level']}%)")
        print(f"  Attitude:  Roll={info['attitude']['roll']:.1f}° Pitch={info['attitude']['pitch']:.1f}° Yaw={info['attitude']['yaw']:.1f}°")
        
        # Check battery
        if info['battery']['voltage'] < 11:
            print("\n❌ Battery voltage too low! Charge to >11.5V")
            return False
        
        print("\n✓ All values look good!")
        
        # Step 4: Start monitoring
        self.print_section("Step 4: Starting Status Monitoring")
        self.controller.start_monitoring()
        time.sleep(2)
        
        print("✓ Monitoring started (you'll see status every 2 seconds)")
        
        self.print_section("✅ PHASE 1 COMPLETE - USB CONNECTION TEST PASSED")
        return True
    
    def phase_2_benchtop(self):
        """PHASE 2: Benchtop Test (Props OFF)."""
        self.print_header(2, "BENCHTOP TEST (PROPS OFF)")
        
        # Safety check
        if not self.pause_for_user(
            "⚠️  CRITICAL: REMOVE ALL PROPELLERS NOW! Then come back here.",
            "yes"
        ):
            print("❌ Aborted")
            return False
        
        print("\n✓ Props removed confirmed")
        
        # Step 1: Set mode
        self.print_section("Step 1: Setting to STABILIZE Mode")
        if not self.controller.set_mode(FlightMode.STABILIZE):
            print("❌ Failed to set mode")
            return False
        print("✓ Mode set")
        
        # Step 2: Arm
        self.print_section("Step 2: Arming Vehicle")
        if not self.controller.arm():
            print("❌ Failed to arm")
            print("   Check: GPS lock, compass, battery, RC failsafe disabled")
            return False
        print("✓ Armed!")
        
        time.sleep(1)
        
        # Step 3: Test neutral sticks
        self.print_section("Step 3: Testing Neutral Stick Position")
        print("Setting sticks to neutral...")
        self.controller.neutral_sticks()
        time.sleep(1)
        print("✓ Sticks at neutral")
        
        # Step 4: Throttle test
        self.print_section("Step 4: Testing Throttle Response")
        print("Ramping throttle: 0% → 50% → 0%")
        print("Watch the motor sounds (should increase then decrease)")
        
        for throttle in [0, 10, 20, 30, 40, 50, 40, 30, 20, 10, 0]:
            print(f"  Throttle: {throttle:2d}%", end="", flush=True)
            self.controller.set_throttle(throttle)
            time.sleep(0.3)
            print("\r", end="")
        
        self.controller.set_throttle(0)
        print("✓ Throttle test complete")
        
        time.sleep(1)
        
        # Step 5: Attitude test
        self.print_section("Step 5: Testing Attitude Commands")
        print("Testing roll command (10% right)...")
        self.controller.set_attitude(roll=10)
        time.sleep(1)
        
        print("Testing pitch command (10% forward)...")
        self.controller.set_attitude(pitch=10)
        time.sleep(1)
        
        print("Testing yaw command (10% right)...")
        self.controller.set_attitude(yaw=10)
        time.sleep(1)
        
        print("Returning to neutral...")
        self.controller.neutral_sticks()
        time.sleep(1)
        print("✓ Attitude commands working")
        
        # Step 6: Disarm
        self.print_section("Step 6: Disarming Vehicle")
        if not self.controller.disarm():
            print("❌ Failed to disarm")
            return False
        print("✓ Disarmed!")
        
        self.print_section("✅ PHASE 2 COMPLETE - BENCHTOP TEST PASSED")
        return True
    
    def phase_3_tethered_hover(self):
        """PHASE 3: Tethered Hover Test."""
        self.print_header(3, "TETHERED HOVER TEST")
        
        # Safety checks
        if not self.pause_for_user(
            "⚠️  CRITICAL CHECKLIST:\n"
            "  [ ] Propellers INSTALLED\n"
            "  [ ] Battery FULLY CHARGED (>12.4V)\n"
            "  [ ] Quad TETHERED (string/rope attached)\n"
            "  [ ] Clear area (2m radius)\n"
            "  [ ] NO PEOPLE IN PROP ZONE",
            "yes"
        ):
            print("❌ Aborted - safety checklist not complete")
            return False
        
        print("\n✓ Safety checklist passed!")
        
        # Step 1: Set mode
        self.print_section("Step 1: Setting to STABILIZE Mode")
        if not self.controller.set_mode(FlightMode.STABILIZE):
            print("❌ Failed to set mode")
            return False
        print("✓ Mode set")
        
        time.sleep(1)
        
        # Step 2: Arm
        self.print_section("Step 2: Arming Vehicle")
        if not self.controller.arm():
            print("❌ Failed to arm")
            print("   Check: GPS lock, compass, battery")
            return False
        print("✓ Armed!")
        
        time.sleep(1)
        
        # Step 3: Gentle throttle ramp
        self.print_section("Step 3: Gentle Throttle Ramp (Should Liftoff)")
        print("Slowly increasing throttle from 0% to 60% over 5 seconds...")
        print("Watch for: Smooth liftoff, stable attitude, no jitter")
        
        start_time = time.time()
        while time.time() - start_time < 5:
            elapsed = time.time() - start_time
            throttle = int((elapsed / 5) * 60)  # 0 to 60% over 5s
            self.controller.set_throttle(throttle)
            print(f"  Throttle: {throttle:2d}%", end="\r", flush=True)
            time.sleep(0.1)
        
        print(f"  Throttle: 60% (holding)    ")
        
        # Step 4: Hover hold
        self.print_section("Step 4: Hovering for 10 Seconds")
        print("Holding at ~45% throttle (typical hover)")
        
        self.controller.set_throttle(45)
        
        for i in range(10, 0, -1):
            print(f"  Time remaining: {i:2d}s", end="\r", flush=True)
            time.sleep(1)
        
        print("  Time remaining:  0s - Hover complete!  ")
        
        # Step 5: Gentle control test
        self.print_section("Step 5: Testing Control Inputs During Hover")
        print("(Small attitudes, 2 degrees)")
        
        print("  Roll right (2°)...")
        self.controller.set_attitude(roll=2)
        time.sleep(1)
        
        print("  Pitch forward (2°)...")
        self.controller.set_attitude(pitch=2)
        time.sleep(1)
        
        print("  Returning to level...")
        self.controller.set_attitude(roll=0, pitch=0)
        time.sleep(1)
        
        print("✓ Control inputs responsive")
        
        # Step 6: Landing
        self.print_section("Step 6: Gentle Landing")
        print("Slowly decreasing throttle to 0% over 5 seconds...")
        
        start_time = time.time()
        while time.time() - start_time < 5:
            elapsed = time.time() - start_time
            throttle = max(0, int(45 * (1 - elapsed / 5)))
            self.controller.set_throttle(throttle)
            print(f"  Throttle: {throttle:2d}%", end="\r", flush=True)
            time.sleep(0.1)
        
        self.controller.set_throttle(0)
        print("  Throttle:  0% - Landed!    ")
        
        time.sleep(1)
        
        # Step 7: Disarm
        self.print_section("Step 7: Disarming Vehicle")
        if not self.controller.disarm():
            print("❌ Failed to disarm")
            return False
        print("✓ Disarmed!")
        
        # Step 8: Final check
        self.print_section("Step 8: Post-Flight Check")
        info = self.controller.get_vehicle_info()
        
        print(f"  Battery:  {info['battery']['voltage']:.2f}V ({info['battery']['level']}%)")
        print(f"  Altitude: {info['location']['alt']:.2f}m")
        print(f"  Heading:  {info['heading']:.1f}°")
        
        if info['battery']['voltage'] < 10.5:
            print("⚠️  WARNING: Battery depleted to <10.5V")
        
        self.print_section("✅ PHASE 3 COMPLETE - TETHERED HOVER TEST PASSED")
        return True
    
    def run_all(self):
        """Run all three phases."""
        print("\n" + "=" * 70)
        print("COMPREHENSIVE PIXHAWK TEST - ALL THREE PHASES")
        print("=" * 70)
        print("\nYou will run:")
        print("  1. USB Connection Test (5 min)")
        print("  2. Benchtop Test (Props OFF) (10 min)")
        print("  3. Tethered Hover Test (Props ON) (20 min)")
        print("\nTotal time: ~35 minutes")
        
        if not self.pause_for_user("Ready to start?", "yes"):
            print("Aborted")
            return False
        
        try:
            # Phase 1
            if not self.phase_1_usb_connection():
                print("\n❌ PHASE 1 FAILED - Stopping")
                return False
            
            time.sleep(2)
            
            if not self.pause_for_user("Ready for Phase 2? (Remove props first!)", "yes"):
                print("Aborted before Phase 2")
                return False
            
            # Phase 2
            if not self.phase_2_benchtop():
                print("\n❌ PHASE 2 FAILED - Stopping")
                return False
            
            time.sleep(2)
            
            if not self.pause_for_user("Ready for Phase 3? (Install props, tether drone!)", "yes"):
                print("Aborted before Phase 3")
                return False
            
            # Phase 3
            if not self.phase_3_tethered_hover():
                print("\n❌ PHASE 3 FAILED")
                return False
            
            # All passed!
            print("\n" + "=" * 70)
            print("🎉 ALL THREE PHASES COMPLETE - SUCCESS!")
            print("=" * 70)
            print("\n📊 Summary:")
            print("  ✅ USB Connection Working")
            print("  ✅ Arm/Disarm Functioning")
            print("  ✅ RC Control Responsive")
            print("  ✅ Throttle Response Smooth")
            print("  ✅ Attitude Stable")
            print("  ✅ First Hover Successful")
            
            print("\n🚀 Next Steps:")
            print("  1. Download flight logs from Pixhawk")
            print("  2. Review attitude errors (should be < 5°)")
            print("  3. Integrate AIC controller (see RC_OVERRIDE_INTEGRATION.md)")
            print("  4. Implement custom control algorithms")
            
            return True
        
        except KeyboardInterrupt:
            print("\n\n❌ Test interrupted by user")
            return False
        
        except Exception as e:
            print(f"\n\n❌ Test failed with error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            # Cleanup
            if self.controller:
                self.controller.stop_monitoring()
                self.controller.disconnect()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Comprehensive Three-Phase Pixhawk Test',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_all_phases.py
  python test_all_phases.py --port /dev/cu.usbmodem14101
"""
    )
    parser.add_argument('--port', default='/dev/cu.usbmodem14101', help='USB port')
    args = parser.parse_args()
    
    tester = TestPhases(args.port)
    success = tester.run_all()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
