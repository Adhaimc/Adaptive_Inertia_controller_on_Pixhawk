"""
Safety Manager for Erle-Brain 2 autonomous flight system.
Handles pre-flight checks, battery monitoring, geofencing, and failsafes.
"""

import time
import math
from typing import Tuple, Dict, Optional
from dronekit import Vehicle, LocationGlobalRelative

from utils.logger import get_logger
from utils.config import get_config


class SafetyManager:
    """Manages safety checks and failsafes for autonomous flight."""
    
    def __init__(self, vehicle: Vehicle):
        """
        Initialize safety manager.
        
        Args:
            vehicle: Connected DroneKit vehicle instance
        """
        self.vehicle = vehicle
        self.config = get_config()
        self.logger = get_logger()
        
        # Safety parameters from config
        self.battery_critical = self.config.get('safety.battery_critical', 10.5)
        self.battery_warning = self.config.get('safety.battery_warning', 11.1)
        self.gps_min_satellites = self.config.get('safety.gps_min_satellites', 6)
        self.gps_min_hdop = self.config.get('safety.gps_min_hdop', 2.0)
        
        # Geofence parameters
        self.geofence_enabled = self.config.get('geofence.enabled', True)
        self.geofence_radius = self.config.get('geofence.radius', 100.0)
        self.geofence_max_alt = self.config.get('geofence.max_altitude', 50.0)
        self.geofence_min_alt = self.config.get('geofence.min_altitude', 2.0)
        
        # Home location for geofence center
        self.home_location: Optional[LocationGlobalRelative] = None
        
        # Warning flags
        self.low_battery_warning_issued = False
        self.geofence_warning_issued = False
    
    def pre_flight_checks(self) -> Tuple[bool, str]:
        """
        Perform comprehensive pre-flight safety checks.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        self.logger.info("=" * 60)
        self.logger.info("PRE-FLIGHT SAFETY CHECKS")
        self.logger.info("=" * 60)
        
        checks = [
            ("GPS Lock", self.check_gps_lock),
            ("Battery Level", self.check_battery),
            ("Home Position", self.check_home_position),
            ("Sensor Health", self.check_sensors),
            ("RC Connection", self.check_rc_connection),
            ("Flight Mode", self.check_flight_mode)
        ]
        
        failed_checks = []
        
        for check_name, check_func in checks:
            self.logger.info(f"\nChecking: {check_name}...")
            success, message = check_func()
            
            if success:
                self.logger.info(f"  ✓ {check_name}: PASS - {message}")
            else:
                self.logger.log_safety_event(f"{check_name}: FAIL - {message}", 'ERROR')
                failed_checks.append(check_name)
        
        self.logger.info("\n" + "=" * 60)
        
        if failed_checks:
            failure_msg = f"Pre-flight checks failed: {', '.join(failed_checks)}"
            self.logger.log_safety_event(failure_msg, 'CRITICAL')
            return False, failure_msg
        else:
            self.logger.info("✓ All pre-flight checks passed!")
            self.logger.info("=" * 60)
            return True, "All checks passed"
    
    def check_gps_lock(self) -> Tuple[bool, str]:
        """
        Check GPS lock status.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            gps = self.vehicle.gps_0
            
            if gps is None:
                return False, "GPS module not detected"
            
            fix_type = gps.fix_type
            satellites = gps.satellites_visible
            hdop = gps.eph / 100.0 if gps.eph else 99.99  # Convert to HDOP
            
            # Fix type: 0=No GPS, 1=No Fix, 2=2D Fix, 3=3D Fix
            if fix_type < 2:
                return False, f"No GPS fix (fix_type: {fix_type})"
            
            if satellites < self.gps_min_satellites:
                return False, f"Insufficient satellites: {satellites}/{self.gps_min_satellites}"
            
            if hdop > self.gps_min_hdop:
                return False, f"HDOP too high: {hdop:.2f} (max: {self.gps_min_hdop})"
            
            return True, f"GPS OK (Fix: {fix_type}, Sats: {satellites}, HDOP: {hdop:.2f})"
            
        except Exception as e:
            return False, f"GPS check error: {str(e)}"
    
    def check_battery(self) -> Tuple[bool, str]:
        """
        Check battery level.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            battery = self.vehicle.battery
            
            if battery is None:
                return False, "Battery monitoring not available"
            
            voltage = battery.voltage
            level = battery.level
            
            if voltage < self.battery_critical:
                return False, f"Battery critical: {voltage:.2f}V (min: {self.battery_critical}V)"
            
            if voltage < self.battery_warning:
                return True, f"Battery low but acceptable: {voltage:.2f}V ({level}%)"
            
            return True, f"Battery OK: {voltage:.2f}V ({level}%)"
            
        except Exception as e:
            return False, f"Battery check error: {str(e)}"
    
    def check_home_position(self) -> Tuple[bool, str]:
        """
        Check if home position is set.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            home = self.vehicle.home_location
            
            if home is None or (home.lat == 0 and home.lon == 0):
                return False, "Home position not set"
            
            self.home_location = home
            return True, f"Home set: {home.lat:.6f}, {home.lon:.6f}"
            
        except Exception as e:
            return False, f"Home position check error: {str(e)}"
    
    def check_sensors(self) -> Tuple[bool, str]:
        """
        Check sensor health.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Check if we can read basic sensor data
            attitude = self.vehicle.attitude
            velocity = self.vehicle.velocity
            
            if attitude is None or velocity is None:
                return False, "Sensor data not available"
            
            return True, "All sensors responding"
            
        except Exception as e:
            return False, f"Sensor check error: {str(e)}"
    
    def check_rc_connection(self) -> Tuple[bool, str]:
        """
        Check RC connection (if required).
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Check if RC override is possible
            channels = self.vehicle.channels
            
            if channels is None or channels['1'] == 0:
                if self.config.get('safety.check_rc_connection', True):
                    return False, "RC not connected"
                else:
                    return True, "RC check skipped (not required)"
            
            return True, f"RC connected (channels active)"
            
        except Exception as e:
            # RC might not be required for autonomous flight
            if self.config.get('safety.check_rc_connection', True):
                return False, f"RC check error: {str(e)}"
            else:
                return True, "RC check skipped"
    
    def check_flight_mode(self) -> Tuple[bool, str]:
        """
        Check if vehicle is in appropriate flight mode.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            mode = self.vehicle.mode.name
            
            # Valid modes for autonomous flight
            valid_modes = ['GUIDED', 'AUTO', 'LOITER', 'STABILIZE']
            
            if mode not in valid_modes:
                return False, f"Invalid mode: {mode} (expected one of {valid_modes})"
            
            return True, f"Mode OK: {mode}"
            
        except Exception as e:
            return False, f"Mode check error: {str(e)}"
    
    def monitor_battery(self) -> Optional[str]:
        """
        Monitor battery level during flight.
        
        Returns:
            Warning message if battery is low, None otherwise
        """
        try:
            battery = self.vehicle.battery
            if battery is None:
                return None
            
            voltage = battery.voltage
            
            if voltage < self.battery_critical:
                self.logger.log_safety_event(
                    f"CRITICAL: Battery voltage {voltage:.2f}V - RTL required!",
                    'CRITICAL'
                )
                return "CRITICAL_BATTERY"
            
            if voltage < self.battery_warning and not self.low_battery_warning_issued:
                self.logger.log_safety_event(
                    f"WARNING: Battery voltage {voltage:.2f}V - Consider RTL",
                    'WARNING'
                )
                self.low_battery_warning_issued = True
                return "LOW_BATTERY"
            
            return None
            
        except Exception as e:
            self.logger.error(f"Battery monitoring error: {str(e)}")
            return None
    
    def check_geofence(self) -> Optional[str]:
        """
        Check if vehicle is within geofence boundaries.
        
        Returns:
            Warning message if geofence is breached, None otherwise
        """
        if not self.geofence_enabled or self.home_location is None:
            return None
        
        try:
            current_location = self.vehicle.location.global_relative_frame
            current_alt = current_location.alt
            
            # Check altitude fence
            if current_alt > self.geofence_max_alt:
                self.logger.log_safety_event(
                    f"Altitude fence breached: {current_alt:.1f}m > {self.geofence_max_alt}m",
                    'CRITICAL'
                )
                return "ALTITUDE_FENCE_BREACH"
            
            if current_alt < self.geofence_min_alt and current_alt > 0.5:
                self.logger.log_safety_event(
                    f"Minimum altitude breached: {current_alt:.1f}m < {self.geofence_min_alt}m",
                    'WARNING'
                )
            
            # Check horizontal distance from home
            distance = self._get_distance(
                self.home_location.lat, self.home_location.lon,
                current_location.lat, current_location.lon
            )
            
            if distance > self.geofence_radius:
                self.logger.log_safety_event(
                    f"Horizontal fence breached: {distance:.1f}m > {self.geofence_radius}m",
                    'CRITICAL'
                )
                return "HORIZONTAL_FENCE_BREACH"
            
            # Warning when approaching fence
            if distance > self.geofence_radius * 0.9 and not self.geofence_warning_issued:
                self.logger.log_safety_event(
                    f"Approaching geofence: {distance:.1f}m / {self.geofence_radius}m",
                    'WARNING'
                )
                self.geofence_warning_issued = True
            
            return None
            
        except Exception as e:
            self.logger.error(f"Geofence check error: {str(e)}")
            return None
    
    def _get_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two GPS coordinates in meters.
        
        Args:
            lat1, lon1: First coordinate
            lat2, lon2: Second coordinate
        
        Returns:
            Distance in meters
        """
        # Haversine formula
        R = 6371000  # Earth radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def continuous_safety_monitor(self) -> Dict[str, Optional[str]]:
        """
        Perform continuous safety monitoring during flight.
        
        Returns:
            Dictionary of safety alerts
        """
        alerts = {
            'battery': self.monitor_battery(),
            'geofence': self.check_geofence()
        }
        
        return {k: v for k, v in alerts.items() if v is not None}


if __name__ == '__main__':
    print("Safety Manager module - use with autonomous_flight.py")
