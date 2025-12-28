"""
Telemetry Monitor for Erle-Brain 2 autonomous flight system.
Real-time monitoring and display of vehicle telemetry data.
"""

import time
import threading
from typing import Dict, Optional
from dronekit import Vehicle

from utils.logger import get_logger, TelemetryLogger
from utils.config import get_config


class TelemetryMonitor:
    """Real-time telemetry monitoring and logging."""
    
    def __init__(self, vehicle: Vehicle, enable_csv_logging: bool = True):
        """
        Initialize telemetry monitor.
        
        Args:
            vehicle: Connected DroneKit vehicle instance
            enable_csv_logging: Enable CSV telemetry logging
        """
        self.vehicle = vehicle
        self.config = get_config()
        self.logger = get_logger()
        
        # CSV logger for detailed telemetry
        self.telemetry_logger = TelemetryLogger() if enable_csv_logging else None
        
        # Monitoring control
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # Update rates from config
        self.update_interval = 1.0 / self.config.get('telemetry.position_rate', 10)
        self.verbose = self.config.get('telemetry.verbose', True)
    
    def get_current_telemetry(self) -> Dict:
        """
        Get current telemetry snapshot.
        
        Returns:
            Dictionary containing all telemetry data
        """
        try:
            # Location
            location = self.vehicle.location.global_relative_frame
            
            # Velocity
            velocity = self.vehicle.velocity
            
            # Attitude
            attitude = self.vehicle.attitude
            
            # GPS
            gps = self.vehicle.gps_0
            
            # Battery
            battery = self.vehicle.battery
            
            telemetry = {
                # Flight status
                'mode': self.vehicle.mode.name,
                'armed': self.vehicle.armed,
                'is_armable': self.vehicle.is_armable,
                'system_status': self.vehicle.system_status.state,
                
                # Position
                'lat': location.lat if location else 0.0,
                'lon': location.lon if location else 0.0,
                'alt_relative': location.alt if location else 0.0,
                'alt_absolute': self.vehicle.location.global_frame.alt if self.vehicle.location.global_frame else 0.0,
                
                # Velocity (m/s)
                'vx': velocity[0] if velocity and len(velocity) > 0 else 0.0,
                'vy': velocity[1] if velocity and len(velocity) > 1 else 0.0,
                'vz': velocity[2] if velocity and len(velocity) > 2 else 0.0,
                'groundspeed': self.vehicle.groundspeed,
                'airspeed': self.vehicle.airspeed,
                
                # Attitude (radians)
                'roll': attitude.roll if attitude else 0.0,
                'pitch': attitude.pitch if attitude else 0.0,
                'yaw': attitude.yaw if attitude else 0.0,
                'heading': self.vehicle.heading,
                
                # GPS
                'gps_fix': gps.fix_type if gps else 0,
                'gps_sats': gps.satellites_visible if gps else 0,
                'gps_hdop': (gps.eph / 100.0) if gps and gps.eph else 99.99,
                
                # Battery
                'battery_voltage': battery.voltage if battery else 0.0,
                'battery_current': battery.current if battery else 0.0,
                'battery_level': battery.level if battery else 0,
            }
            
            return telemetry
            
        except Exception as e:
            self.logger.error(f"Error getting telemetry: {str(e)}")
            return {}
    
    def print_telemetry(self, telemetry: Dict) -> None:
        """
        Print formatted telemetry to console.
        
        Args:
            telemetry: Telemetry data dictionary
        """
        print("\n" + "=" * 80)
        print(f"{'TELEMETRY DATA':^80}")
        print("=" * 80)
        
        # Flight Status
        print(f"\n{'FLIGHT STATUS':^80}")
        print("-" * 80)
        print(f"Mode: {telemetry.get('mode', 'UNKNOWN'):<15} Armed: {telemetry.get('armed', False):<8} "
              f"Armable: {telemetry.get('is_armable', False):<8}")
        print(f"System Status: {telemetry.get('system_status', 'UNKNOWN')}")
        
        # Position
        print(f"\n{'POSITION':^80}")
        print("-" * 80)
        print(f"Latitude:  {telemetry.get('lat', 0.0):>12.7f}°")
        print(f"Longitude: {telemetry.get('lon', 0.0):>12.7f}°")
        print(f"Altitude (relative): {telemetry.get('alt_relative', 0.0):>8.2f} m")
        print(f"Altitude (absolute): {telemetry.get('alt_absolute', 0.0):>8.2f} m")
        
        # Velocity
        print(f"\n{'VELOCITY':^80}")
        print("-" * 80)
        print(f"Ground Speed: {telemetry.get('groundspeed', 0.0):>6.2f} m/s    "
              f"Air Speed: {telemetry.get('airspeed', 0.0):>6.2f} m/s")
        print(f"Velocity - X: {telemetry.get('vx', 0.0):>6.2f} m/s  "
              f"Y: {telemetry.get('vy', 0.0):>6.2f} m/s  "
              f"Z: {telemetry.get('vz', 0.0):>6.2f} m/s")
        
        # Attitude
        print(f"\n{'ATTITUDE':^80}")
        print("-" * 80)
        roll_deg = telemetry.get('roll', 0.0) * 57.2958  # rad to deg
        pitch_deg = telemetry.get('pitch', 0.0) * 57.2958
        yaw_deg = telemetry.get('yaw', 0.0) * 57.2958
        print(f"Roll:  {roll_deg:>7.2f}°    Pitch: {pitch_deg:>7.2f}°    Yaw: {yaw_deg:>7.2f}°")
        print(f"Heading: {telemetry.get('heading', 0):>3d}°")
        
        # GPS
        print(f"\n{'GPS':^80}")
        print("-" * 80)
        gps_fix_types = {0: 'No GPS', 1: 'No Fix', 2: '2D Fix', 3: '3D Fix'}
        gps_fix = telemetry.get('gps_fix', 0)
        print(f"Fix Type: {gps_fix_types.get(gps_fix, 'Unknown'):<10} "
              f"Satellites: {telemetry.get('gps_sats', 0):>2d}    "
              f"HDOP: {telemetry.get('gps_hdop', 99.99):>5.2f}")
        
        # Battery
        print(f"\n{'BATTERY':^80}")
        print("-" * 80)
        voltage = telemetry.get('battery_voltage', 0.0)
        current = telemetry.get('battery_current', 0.0)
        level = telemetry.get('battery_level', 0)
        print(f"Voltage: {voltage:>5.2f} V    Current: {current:>6.2f} A    Level: {level:>3d}%")
        
        print("=" * 80 + "\n")
    
    def start_monitoring(self, interval: Optional[float] = None) -> None:
        """
        Start continuous telemetry monitoring in background thread.
        
        Args:
            interval: Update interval in seconds (uses config default if None)
        """
        if self.monitoring:
            self.logger.warning("Monitoring already active")
            return
        
        if interval:
            self.update_interval = interval
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        self.logger.info(f"Telemetry monitoring started (interval: {self.update_interval:.2f}s)")
    
    def stop_monitoring(self) -> None:
        """Stop continuous telemetry monitoring."""
        if not self.monitoring:
            return
        
        self.monitoring = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        
        self.logger.info("Telemetry monitoring stopped")
    
    def _monitor_loop(self) -> None:
        """Background monitoring loop."""
        while self.monitoring:
            try:
                telemetry = self.get_current_telemetry()
                
                # Log to CSV if enabled
                if self.telemetry_logger:
                    self.telemetry_logger.log(telemetry)
                
                # Print to console if verbose
                if self.verbose:
                    self.print_telemetry(telemetry)
                else:
                    # Just log key data
                    self.logger.log_telemetry({
                        'mode': telemetry.get('mode'),
                        'alt': f"{telemetry.get('alt_relative', 0.0):.1f}m",
                        'spd': f"{telemetry.get('groundspeed', 0.0):.1f}m/s",
                        'bat': f"{telemetry.get('battery_voltage', 0.0):.1f}V",
                        'sats': telemetry.get('gps_sats', 0)
                    })
                
                time.sleep(self.update_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(1.0)
    
    def monitor_once(self) -> None:
        """Get and display telemetry once."""
        telemetry = self.get_current_telemetry()
        self.print_telemetry(telemetry)
        
        if self.telemetry_logger:
            self.telemetry_logger.log(telemetry)


def main():
    """Test telemetry monitoring with a connected vehicle."""
    import sys
    from utils.connection import VehicleConnection
    
    logger = get_logger()
    
    connection_string = sys.argv[1] if len(sys.argv) > 1 else None
    
    try:
        logger.info("Connecting to vehicle...")
        conn = VehicleConnection(connection_string)
        vehicle = conn.connect()
        
        monitor = TelemetryMonitor(vehicle)
        
        logger.info("Monitoring telemetry for 30 seconds...")
        logger.info("Press Ctrl+C to stop")
        
        monitor.start_monitoring()
        
        try:
            time.sleep(30)
        except KeyboardInterrupt:
            logger.info("\nStopping...")
        
        monitor.stop_monitoring()
        conn.disconnect()
        
        logger.info("Telemetry monitoring test completed")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
