#!/usr/bin/env python3
"""
Example script demonstrating basic autonomous flight operations.
This shows how to use the autonomous flight system step by step.
"""

import time
from src.autonomous_flight import AutonomousController
from src.utils.logger import get_logger

def example_simple_hover():
    """
    Example 1: Simple takeoff, hover, and land.
    Good first test for autonomous flight.
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: SIMPLE HOVER")
    print("="*70)
    
    # Create controller (uses connection from config)
    controller = AutonomousController()
    
    try:
        # Connect to vehicle
        print("Connecting to vehicle...")
        if not controller.connect():
            print("Failed to connect!")
            return
        
        # Execute simple flight: takeoff to 5m, hover 10s, land
        print("\nStarting simple hover test...")
        print("Altitude: 5m")
        print("Duration: 10 seconds")
        
        success = controller.execute_simple_flight(altitude=5.0, duration=10.0)
        
        if success:
            print("\n✓ Flight completed successfully!")
        else:
            print("\n✗ Flight failed")
        
    finally:
        controller.disconnect()


def example_manual_control():
    """
    Example 2: Manual step-by-step flight control.
    Demonstrates individual commands.
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: MANUAL STEP-BY-STEP CONTROL")
    print("="*70)
    
    controller = AutonomousController()
    logger = get_logger()
    
    try:
        # Connect
        if not controller.connect():
            return
        
        # Step 1: Arm and takeoff
        logger.info("Step 1: Taking off to 8 meters...")
        if not controller.arm_and_takeoff(8.0):
            logger.error("Takeoff failed!")
            return
        
        # Step 2: Hover
        logger.info("Step 2: Hovering for 5 seconds...")
        time.sleep(5)
        
        # Step 3: Check telemetry
        logger.info("Step 3: Getting current position...")
        telemetry = controller.telemetry.get_current_telemetry()
        logger.info(f"Current altitude: {telemetry['alt_relative']:.1f}m")
        logger.info(f"Battery: {telemetry['battery_voltage']:.1f}V")
        logger.info(f"GPS satellites: {telemetry['gps_sats']}")
        
        # Step 4: Land
        logger.info("Step 4: Landing...")
        controller.land()
        
        logger.info("✓ Manual flight completed!")
        
    finally:
        controller.disconnect()


def example_waypoint_flight():
    """
    Example 3: Fly to specific GPS waypoints.
    Demonstrates programmatic waypoint navigation.
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: WAYPOINT NAVIGATION")
    print("="*70)
    
    controller = AutonomousController()
    logger = get_logger()
    
    try:
        if not controller.connect():
            return
        
        # Takeoff
        logger.info("Taking off...")
        if not controller.arm_and_takeoff(10.0):
            return
        
        # Define waypoints (REPLACE WITH YOUR COORDINATES!)
        waypoints = [
            (37.7749, -122.4194, 10.0),  # Waypoint 1
            (37.7750, -122.4195, 10.0),  # Waypoint 2
            (37.7751, -122.4194, 10.0),  # Waypoint 3
        ]
        
        logger.info(f"Flying to {len(waypoints)} waypoints...")
        
        # Execute waypoint mission
        success = controller.mission.execute_waypoint_mission(
            waypoints=waypoints,
            groundspeed=3.0
        )
        
        if success:
            logger.info("✓ Waypoint mission completed!")
        
        # Return to launch
        logger.info("Returning to launch...")
        controller.return_to_launch()
        
    finally:
        controller.disconnect()


def example_safety_monitoring():
    """
    Example 4: Demonstrate safety monitoring during flight.
    Shows how to check safety alerts.
    """
    print("\n" + "="*70)
    print("EXAMPLE 4: SAFETY MONITORING")
    print("="*70)
    
    controller = AutonomousController()
    logger = get_logger()
    
    try:
        if not controller.connect():
            return
        
        # Pre-flight checks
        logger.info("Running pre-flight safety checks...")
        checks_passed, message = controller.safety.pre_flight_checks()
        
        if not checks_passed:
            logger.error(f"Pre-flight checks failed: {message}")
            return
        
        logger.info("✓ All pre-flight checks passed!")
        
        # Takeoff
        if not controller.arm_and_takeoff(8.0):
            return
        
        # Monitor for 15 seconds with safety checks
        logger.info("Monitoring flight with safety checks for 15 seconds...")
        
        for i in range(15):
            # Get safety alerts
            alerts = controller.safety.continuous_safety_monitor()
            
            if alerts:
                logger.warning(f"Safety alerts detected: {alerts}")
                
                # Handle critical battery
                if 'CRITICAL_BATTERY' in alerts.values():
                    logger.critical("Critical battery! Returning to launch!")
                    controller.return_to_launch()
                    break
            
            # Get telemetry
            telemetry = controller.telemetry.get_current_telemetry()
            logger.info(
                f"Alt: {telemetry['alt_relative']:.1f}m, "
                f"Bat: {telemetry['battery_voltage']:.1f}V, "
                f"Sats: {telemetry['gps_sats']}"
            )
            
            time.sleep(1)
        
        # Land
        controller.land()
        logger.info("✓ Safety monitoring demo completed!")
        
    finally:
        controller.disconnect()


def main():
    """Main menu for examples."""
    print("\n" + "="*70)
    print("ERLE-BRAIN 2 AUTONOMOUS FLIGHT EXAMPLES")
    print("="*70)
    print("\nChoose an example:")
    print("1. Simple Hover (Recommended first)")
    print("2. Manual Step-by-Step Control")
    print("3. Waypoint Navigation")
    print("4. Safety Monitoring Demo")
    print("0. Exit")
    print("\n⚠️  WARNING: Test in simulation first!")
    print("⚠️  Update GPS coordinates in code before real flight!")
    
    try:
        choice = input("\nEnter choice (0-4): ").strip()
        
        if choice == '1':
            example_simple_hover()
        elif choice == '2':
            example_manual_control()
        elif choice == '3':
            print("\n⚠️  WARNING: Update GPS coordinates in the code first!")
            confirm = input("Have you updated coordinates? (yes/no): ")
            if confirm.lower() == 'yes':
                example_waypoint_flight()
            else:
                print("Please update coordinates before running this example.")
        elif choice == '4':
            example_safety_monitoring()
        elif choice == '0':
            print("Goodbye!")
        else:
            print("Invalid choice!")
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user!")
    except Exception as e:
        print(f"\nError: {str(e)}")


if __name__ == '__main__':
    main()
