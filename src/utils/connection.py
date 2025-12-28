"""
Vehicle connection utilities for Erle-Brain 2 autonomous flight system.
Handles DroneKit vehicle connection with error handling and retries.
"""

import time
from typing import Optional
from dronekit import connect, Vehicle, VehicleMode
from pymavlink import mavutil

from .logger import get_logger
from .config import get_config


class VehicleConnection:
    """Manages connection to ArduPilot vehicle via DroneKit."""
    
    def __init__(
        self,
        connection_string: Optional[str] = None,
        baud_rate: int = None,
        timeout: int = None,
        max_retries: int = 3
    ):
        """
        Initialize vehicle connection manager.
        
        Args:
            connection_string: MAVLink connection string
            baud_rate: Baud rate for serial connections
            timeout: Connection timeout in seconds
            max_retries: Maximum connection retry attempts
        """
        self.config = get_config()
        self.logger = get_logger()
        
        # Use provided values or get from config
        self.connection_string = connection_string or self.config.get('connection.default_string')
        self.baud_rate = baud_rate or self.config.get('connection.baud_rate', 921600)
        self.timeout = timeout or self.config.get('connection.timeout', 30)
        self.max_retries = max_retries
        
        self.vehicle: Optional[Vehicle] = None
        self.connected = False
    
    def connect(self) -> Vehicle:
        """
        Connect to vehicle with retry logic.
        
        Returns:
            Connected Vehicle instance
        
        Raises:
            Exception: If connection fails after all retries
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                self.logger.info(f"Connection attempt {attempt}/{self.max_retries}")
                self.logger.log_connection_event(
                    'Connecting',
                    f"Connection string: {self.connection_string}"
                )
                
                # Connect based on connection type
                if self.connection_string.startswith('/dev/'):
                    # Serial connection
                    self.vehicle = connect(
                        self.connection_string,
                        baud=self.baud_rate,
                        wait_ready=True,
                        timeout=self.timeout
                    )
                else:
                    # Network connection (UDP/TCP)
                    self.vehicle = connect(
                        self.connection_string,
                        wait_ready=True,
                        timeout=self.timeout
                    )
                
                self.connected = True
                self.logger.log_connection_event('Connected successfully')
                self._log_vehicle_info()
                
                return self.vehicle
                
            except Exception as e:
                self.logger.error(f"Connection attempt {attempt} failed: {str(e)}")
                
                if attempt < self.max_retries:
                    retry_delay = attempt * 2  # Exponential backoff
                    self.logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    self.logger.critical("All connection attempts failed")
                    raise Exception(f"Failed to connect after {self.max_retries} attempts: {str(e)}")
    
    def _log_vehicle_info(self) -> None:
        """Log basic vehicle information after connection."""
        if self.vehicle:
            info = {
                'Version': f"{self.vehicle.version}",
                'Mode': self.vehicle.mode.name,
                'Armed': self.vehicle.armed,
                'System Status': self.vehicle.system_status.state,
                'Is Armable': self.vehicle.is_armable
            }
            
            self.logger.info("Vehicle Information:")
            for key, value in info.items():
                self.logger.info(f"  {key}: {value}")
    
    def disconnect(self) -> None:
        """Disconnect from vehicle."""
        if self.vehicle:
            try:
                self.logger.log_connection_event('Disconnecting from vehicle')
                self.vehicle.close()
                self.connected = False
                self.logger.log_connection_event('Disconnected successfully')
            except Exception as e:
                self.logger.error(f"Error during disconnect: {str(e)}")
    
    def is_connected(self) -> bool:
        """
        Check if vehicle is connected.
        
        Returns:
            True if connected, False otherwise
        """
        return self.connected and self.vehicle is not None
    
    def get_vehicle(self) -> Optional[Vehicle]:
        """
        Get the connected vehicle instance.
        
        Returns:
            Vehicle instance or None if not connected
        """
        if not self.is_connected():
            self.logger.warning("Attempting to get vehicle but not connected")
            return None
        return self.vehicle
    
    def wait_for_armable(self, timeout: int = 30) -> bool:
        """
        Wait for vehicle to become armable.
        
        Args:
            timeout: Maximum wait time in seconds
        
        Returns:
            True if vehicle is armable, False if timeout
        """
        if not self.vehicle:
            return False
        
        self.logger.info("Waiting for vehicle to become armable...")
        start_time = time.time()
        
        while not self.vehicle.is_armable:
            if time.time() - start_time > timeout:
                self.logger.error(f"Vehicle not armable after {timeout} seconds")
                return False
            
            self.logger.info(f"Waiting for armable state... ({int(time.time() - start_time)}s)")
            time.sleep(1)
        
        self.logger.info("Vehicle is armable")
        return True
    
    def check_connection_health(self) -> bool:
        """
        Check if connection is healthy by verifying heartbeat.
        
        Returns:
            True if connection is healthy, False otherwise
        """
        if not self.vehicle:
            return False
        
        try:
            # Try to access vehicle attribute to check heartbeat
            _ = self.vehicle.location.global_frame
            return True
        except Exception as e:
            self.logger.error(f"Connection health check failed: {str(e)}")
            return False
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


def test_connection(connection_string: str = None) -> bool:
    """
    Test connection to vehicle.
    
    Args:
        connection_string: Optional connection string to test
    
    Returns:
        True if connection successful, False otherwise
    """
    logger = get_logger()
    
    try:
        logger.info("=" * 60)
        logger.info("VEHICLE CONNECTION TEST")
        logger.info("=" * 60)
        
        with VehicleConnection(connection_string) as conn:
            vehicle = conn.get_vehicle()
            
            if vehicle:
                logger.info("\n✓ Connection successful!")
                logger.info("\nVehicle Status:")
                logger.info(f"  Mode: {vehicle.mode.name}")
                logger.info(f"  Armed: {vehicle.armed}")
                logger.info(f"  Is Armable: {vehicle.is_armable}")
                logger.info(f"  System Status: {vehicle.system_status.state}")
                logger.info(f"  Autopilot Version: {vehicle.version}")
                
                if vehicle.battery:
                    logger.info(f"  Battery Voltage: {vehicle.battery.voltage}V")
                    logger.info(f"  Battery Level: {vehicle.battery.level}%")
                
                if vehicle.gps_0:
                    logger.info(f"  GPS Fix Type: {vehicle.gps_0.fix_type}")
                    logger.info(f"  GPS Satellites: {vehicle.gps_0.satellites_visible}")
                
                logger.info("\n" + "=" * 60)
                return True
            else:
                logger.error("Failed to get vehicle instance")
                return False
                
    except Exception as e:
        logger.error(f"Connection test failed: {str(e)}")
        return False


if __name__ == '__main__':
    # Run connection test
    import sys
    
    connection_string = sys.argv[1] if len(sys.argv) > 1 else None
    success = test_connection(connection_string)
    
    sys.exit(0 if success else 1)
