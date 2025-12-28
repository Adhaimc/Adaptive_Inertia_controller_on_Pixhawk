"""
Autonomous Flight Controller for Erle-Brain 2.
Main controller for fully autonomous quadcopter operations.
"""

import time
import argparse
from typing import Optional
from dronekit import Vehicle, VehicleMode

from utils.connection import VehicleConnection
from utils.logger import get_logger
from utils.config import get_config
from safety_manager import SafetyManager
from mission_planner import MissionPlanner
from telemetry_monitor import TelemetryMonitor


class AutonomousController:
    """Main autonomous flight controller."""
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize autonomous controller.
        
        Args:
            connection_string: MAVLink connection string
        """
        self.config = get_config()
        self.logger = get_logger()
        
        # Connection
        self.conn = VehicleConnection(connection_string)
        self.vehicle: Optional[Vehicle] = None
        
        # Component managers
        self.safety: Optional[SafetyManager] = None
        self.mission: Optional[MissionPlanner] = None
        self.telemetry: Optional[TelemetryMonitor] = None
        
        self.logger.info("=" * 70)
        self.logger.info("ERLE-BRAIN 2 AUTONOMOUS FLIGHT CONTROLLER")
        self.logger.info("=" * 70)
    
    def connect(self) -> bool:
        """
        Connect to vehicle and initialize components.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.vehicle = self.conn.connect()
            
            if not self.vehicle:
                return False
            
            # Initialize component managers
            self.safety = SafetyManager(self.vehicle)
            self.mission = MissionPlanner(self.vehicle)
            self.telemetry = TelemetryMonitor(self.vehicle)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Connection failed: {str(e)}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from vehicle."""
        if self.telemetry:
            self.telemetry.stop_monitoring()
        
        self.conn.disconnect()
        self.logger.info("Disconnected from vehicle")
    
    def set_mode(self, mode_name: str, timeout: int = 5) -> bool:
        """
        Set vehicle flight mode.
        
        Args:
            mode_name: Mode name (e.g., 'GUIDED', 'AUTO', 'RTL')
            timeout: Timeout in seconds
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Setting mode to {mode_name}...")
            
            mode = VehicleMode(mode_name)
            self.vehicle.mode = mode
            
            # Wait for mode change
            start_time = time.time()
            while self.vehicle.mode.name != mode_name:
                if time.time() - start_time > timeout:
                    self.logger.error(f"Timeout setting mode to {mode_name}")
                    return False
                time.sleep(0.5)
            
            self.logger.info(f"Mode set to {mode_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set mode: {str(e)}")
            return False
    
    def arm(self, timeout: int = 10) -> bool:
        """
        Arm vehicle motors.
        
        Args:
            timeout: Timeout in seconds
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("Arming vehicle...")
            
            # Pre-arm checks
            if not self.conn.wait_for_armable(timeout):
                self.logger.error("Vehicle not armable")
                return False
            
            # Arm
            self.vehicle.armed = True
            
            # Wait for arming
            start_time = time.time()
            while not self.vehicle.armed:
                if time.time() - start_time > timeout:
                    self.logger.error("Timeout waiting for arm")
                    return False
                self.logger.info("Waiting for arming...")
                time.sleep(1)
            
            self.logger.info("✓ Vehicle armed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to arm: {str(e)}")
            return False
    
    def disarm(self, force: bool = False) -> bool:
        """
        Disarm vehicle motors.
        
        Args:
            force: Force disarm even if in air
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("Disarming vehicle...")
            self.vehicle.armed = False
            
            # Wait for disarm
            timeout = 5
            start_time = time.time()
            while self.vehicle.armed:
                if time.time() - start_time > timeout:
                    if force:
                        self.logger.warning("Force disarming...")
                        # Force disarm via MAVLink command if needed
                    else:
                        self.logger.error("Timeout waiting for disarm")
                        return False
                time.sleep(0.5)
            
            self.logger.info("✓ Vehicle disarmed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to disarm: {str(e)}")
            return False
    
    def arm_and_takeoff(self, target_altitude: float) -> bool:
        """
        Arm vehicle and takeoff to target altitude.
        
        Args:
            target_altitude: Target altitude in meters
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("=" * 70)
            self.logger.info("STARTING AUTONOMOUS TAKEOFF")
            self.logger.info("=" * 70)
            
            # Pre-flight safety checks
            checks_passed, message = self.safety.pre_flight_checks()
            if not checks_passed:
                self.logger.critical(f"Pre-flight checks failed: {message}")
                return False
            
            # Set GUIDED mode
            if not self.set_mode('GUIDED'):
                return False
            
            # Arm vehicle
            if not self.arm():
                return False
            
            # Takeoff
            self.logger.info(f"Taking off to {target_altitude}m...")
            self.vehicle.simple_takeoff(target_altitude)
            
            # Wait for altitude
            while True:
                current_alt = self.vehicle.location.global_relative_frame.alt
                self.logger.info(f"Altitude: {current_alt:.1f}m / {target_altitude}m")
                
                # Check for safety alerts during takeoff
                alerts = self.safety.continuous_safety_monitor()
                if alerts:
                    self.logger.log_safety_event(f"Safety alerts during takeoff: {alerts}", 'WARNING')
                
                if current_alt >= target_altitude * 0.95:
                    self.logger.info("✓ Reached target altitude")
                    break
                
                time.sleep(1)
            
            self.logger.info("=" * 70)
            self.logger.info("TAKEOFF COMPLETE")
            self.logger.info("=" * 70)
            return True
            
        except Exception as e:
            self.logger.error(f"Takeoff failed: {str(e)}")
            return False
    
    def land(self) -> bool:
        """
        Land vehicle at current location.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("=" * 70)
            self.logger.info("STARTING AUTONOMOUS LANDING")
            self.logger.info("=" * 70)
            
            # Set LAND mode
            if not self.set_mode('LAND'):
                return False
            
            # Monitor landing
            landing_threshold = self.config.get('flight.landing_threshold_altitude', 0.3)
            
            while self.vehicle.armed:
                current_alt = self.vehicle.location.global_relative_frame.alt
                self.logger.info(f"Landing... Altitude: {current_alt:.1f}m")
                
                if current_alt < landing_threshold:
                    self.logger.info("Near ground, waiting for disarm...")
                
                time.sleep(1)
            
            self.logger.info("=" * 70)
            self.logger.info("LANDING COMPLETE")
            self.logger.info("=" * 70)
            return True
            
        except Exception as e:
            self.logger.error(f"Landing failed: {str(e)}")
            return False
    
    def return_to_launch(self) -> bool:
        """
        Return to launch location and land.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("=" * 70)
            self.logger.info("RETURN TO LAUNCH")
            self.logger.info("=" * 70)
            
            if not self.set_mode('RTL'):
                return False
            
            # Monitor RTL
            while self.vehicle.armed:
                current_alt = self.vehicle.location.global_relative_frame.alt
                mode = self.vehicle.mode.name
                
                self.logger.info(f"RTL in progress - Mode: {mode}, Alt: {current_alt:.1f}m")
                
                # Check safety
                alerts = self.safety.continuous_safety_monitor()
                if alerts:
                    self.logger.log_safety_event(f"Safety alerts during RTL: {alerts}", 'WARNING')
                
                time.sleep(2)
            
            self.logger.info("=" * 70)
            self.logger.info("RTL COMPLETE")
            self.logger.info("=" * 70)
            return True
            
        except Exception as e:
            self.logger.error(f"RTL failed: {str(e)}")
            return False
    
    def execute_simple_flight(
        self,
        altitude: float = 10.0,
        duration: float = 10.0
    ) -> bool:
        """
        Execute simple test flight: takeoff, hover, land.
        
        Args:
            altitude: Takeoff altitude in meters
            duration: Hover duration in seconds
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("=" * 70)
            self.logger.info("EXECUTING SIMPLE TEST FLIGHT")
            self.logger.info(f"Altitude: {altitude}m, Duration: {duration}s")
            self.logger.info("=" * 70)
            
            # Takeoff
            if not self.arm_and_takeoff(altitude):
                return False
            
            # Hover and monitor
            self.logger.info(f"Hovering for {duration} seconds...")
            start_time = time.time()
            
            while time.time() - start_time < duration:
                elapsed = time.time() - start_time
                remaining = duration - elapsed
                
                current_alt = self.vehicle.location.global_relative_frame.alt
                self.logger.info(
                    f"Hovering... Alt: {current_alt:.1f}m, "
                    f"Time: {elapsed:.0f}s / {duration:.0f}s"
                )
                
                # Safety monitoring
                alerts = self.safety.continuous_safety_monitor()
                if alerts:
                    self.logger.log_safety_event(
                        f"Safety alerts: {alerts}",
                        'WARNING'
                    )
                    
                    # Handle critical alerts
                    if 'CRITICAL_BATTERY' in alerts.values():
                        self.logger.critical("Critical battery! Returning to launch")
                        return self.return_to_launch()
                
                time.sleep(1)
            
            # Land
            return self.land()
            
        except Exception as e:
            self.logger.error(f"Simple flight failed: {str(e)}")
            # Emergency landing
            self.logger.critical("Attempting emergency landing")
            return self.land()
    
    def execute_mission_file(self, mission_file: str) -> bool:
        """
        Execute mission from JSON file.
        
        Args:
            mission_file: Path to mission JSON file
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("=" * 70)
            self.logger.info(f"EXECUTING MISSION: {mission_file}")
            self.logger.info("=" * 70)
            
            # Load mission
            if not self.mission.load_mission_from_file(mission_file):
                return False
            
            # Takeoff
            takeoff_alt = self.config.get('flight.takeoff_altitude', 10.0)
            if not self.arm_and_takeoff(takeoff_alt):
                return False
            
            # Execute waypoints
            default_speed = self.config.get('flight.default_speed', 5.0)
            if not self.mission.execute_waypoint_mission(groundspeed=default_speed):
                self.logger.error("Mission execution failed")
                self.return_to_launch()
                return False
            
            # Return and land
            return self.return_to_launch()
            
        except Exception as e:
            self.logger.error(f"Mission execution failed: {str(e)}")
            self.return_to_launch()
            return False


def main():
    """Main entry point for autonomous flight controller."""
    parser = argparse.ArgumentParser(
        description='Erle-Brain 2 Autonomous Flight Controller'
    )
    parser.add_argument(
        '--connection',
        default=None,
        help='MAVLink connection string (default from config)'
    )
    parser.add_argument(
        '--mission',
        help='Mission JSON file to execute'
    )
    parser.add_argument(
        '--altitude',
        type=float,
        default=10.0,
        help='Flight altitude in meters (default: 10.0)'
    )
    parser.add_argument(
        '--duration',
        type=float,
        default=10.0,
        help='Hover duration in seconds (default: 10.0)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run simple test flight'
    )
    
    args = parser.parse_args()
    
    # Create controller
    controller = AutonomousController(args.connection)
    
    try:
        # Connect
        if not controller.connect():
            print("Failed to connect to vehicle")
            return 1
        
        # Execute mission or test flight
        if args.mission:
            success = controller.execute_mission_file(args.mission)
        elif args.test:
            success = controller.execute_simple_flight(args.altitude, args.duration)
        else:
            print("No mission specified. Use --mission or --test")
            print("Run with --help for options")
            controller.disconnect()
            return 1
        
        # Disconnect
        controller.disconnect()
        
        if success:
            print("\n✓ Flight completed successfully")
            return 0
        else:
            print("\n✗ Flight failed")
            return 1
        
    except KeyboardInterrupt:
        print("\n\nFlight interrupted by user!")
        controller.logger.critical("Emergency: User interrupt")
        
        # Emergency landing
        if controller.vehicle and controller.vehicle.armed:
            controller.logger.critical("Attempting emergency landing...")
            controller.land()
        
        controller.disconnect()
        return 1
    
    except Exception as e:
        print(f"\nFatal error: {str(e)}")
        controller.logger.critical(f"Fatal error: {str(e)}")
        
        # Emergency landing
        if controller.vehicle and controller.vehicle.armed:
            controller.logger.critical("Attempting emergency landing...")
            try:
                controller.land()
            except:
                pass
        
        controller.disconnect()
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
