"""
Logging utilities for Erle-Brain 2 autonomous flight system.
Provides formatted logging with file and console output.
"""

import os
import logging
import sys
from datetime import datetime
from typing import Optional


class FlightLogger:
    """Custom logger for flight operations with file and console output."""
    
    def __init__(
        self,
        name: str = 'autonomous_flight',
        log_dir: str = 'logs',
        log_level: str = 'INFO',
        console_output: bool = True
    ):
        """
        Initialize flight logger.
        
        Args:
            name: Logger name
            log_dir: Directory for log files
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            console_output: Enable console output
        """
        self.name = name
        self.log_dir = log_dir
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.console_output = console_output
        
        # Create log directory if it doesn't exist
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Create logger
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """
        Set up logger with file and console handlers.
        
        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(self.name)
        logger.setLevel(self.log_level)
        
        # Clear any existing handlers
        logger.handlers.clear()
        
        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # File handler - create new log file for each session
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(self.log_dir, f'{self.name}_{timestamp}.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # Console handler
        if self.console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.log_level)
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        logger.info(f"Logger initialized. Log file: {log_file}")
        
        return logger
    
    def debug(self, message: str) -> None:
        """Log debug message."""
        self.logger.debug(message)
    
    def info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(message)
    
    def warning(self, message: str) -> None:
        """Log warning message."""
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        """Log error message."""
        self.logger.error(message)
    
    def critical(self, message: str) -> None:
        """Log critical message."""
        self.logger.critical(message)
    
    def log_telemetry(self, data: dict) -> None:
        """
        Log telemetry data in a structured format.
        
        Args:
            data: Dictionary containing telemetry data
        """
        message = " | ".join([f"{key}: {value}" for key, value in data.items()])
        self.logger.info(f"TELEMETRY | {message}")
    
    def log_mission_event(self, event: str, details: Optional[str] = None) -> None:
        """
        Log mission events.
        
        Args:
            event: Event name
            details: Additional details
        """
        if details:
            self.logger.info(f"MISSION | {event} | {details}")
        else:
            self.logger.info(f"MISSION | {event}")
    
    def log_safety_event(self, event: str, level: str = 'WARNING') -> None:
        """
        Log safety-related events.
        
        Args:
            event: Safety event description
            level: Log level (INFO, WARNING, ERROR, CRITICAL)
        """
        log_func = getattr(self.logger, level.lower(), self.logger.warning)
        log_func(f"SAFETY | {event}")
    
    def log_connection_event(self, event: str, details: Optional[str] = None) -> None:
        """
        Log connection-related events.
        
        Args:
            event: Connection event description
            details: Additional details
        """
        if details:
            self.logger.info(f"CONNECTION | {event} | {details}")
        else:
            self.logger.info(f"CONNECTION | {event}")


class TelemetryLogger:
    """Specialized logger for continuous telemetry data."""
    
    def __init__(self, log_dir: str = 'logs'):
        """
        Initialize telemetry logger.
        
        Args:
            log_dir: Directory for log files
        """
        self.log_dir = log_dir
        
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.telemetry_file = os.path.join(log_dir, f'telemetry_{timestamp}.csv')
        
        # Create CSV header
        self._create_header()
    
    def _create_header(self) -> None:
        """Create CSV header for telemetry file."""
        header = (
            "timestamp,mode,armed,alt_relative,alt_absolute,"
            "lat,lon,vx,vy,vz,heading,groundspeed,airspeed,"
            "battery_voltage,battery_current,battery_level,"
            "gps_fix,gps_sats,gps_hdop,roll,pitch,yaw\n"
        )
        with open(self.telemetry_file, 'w') as f:
            f.write(header)
    
    def log(self, telemetry_data: dict) -> None:
        """
        Log telemetry data to CSV file.
        
        Args:
            telemetry_data: Dictionary containing telemetry data
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        # Extract data with defaults
        row = [
            timestamp,
            telemetry_data.get('mode', 'UNKNOWN'),
            telemetry_data.get('armed', False),
            telemetry_data.get('alt_relative', 0.0),
            telemetry_data.get('alt_absolute', 0.0),
            telemetry_data.get('lat', 0.0),
            telemetry_data.get('lon', 0.0),
            telemetry_data.get('vx', 0.0),
            telemetry_data.get('vy', 0.0),
            telemetry_data.get('vz', 0.0),
            telemetry_data.get('heading', 0.0),
            telemetry_data.get('groundspeed', 0.0),
            telemetry_data.get('airspeed', 0.0),
            telemetry_data.get('battery_voltage', 0.0),
            telemetry_data.get('battery_current', 0.0),
            telemetry_data.get('battery_level', 0),
            telemetry_data.get('gps_fix', 0),
            telemetry_data.get('gps_sats', 0),
            telemetry_data.get('gps_hdop', 99.99),
            telemetry_data.get('roll', 0.0),
            telemetry_data.get('pitch', 0.0),
            telemetry_data.get('yaw', 0.0)
        ]
        
        line = ','.join(str(x) for x in row) + '\n'
        
        with open(self.telemetry_file, 'a') as f:
            f.write(line)


# Singleton instance for easy access
_logger_instance = None


def get_logger(
    name: str = 'autonomous_flight',
    log_dir: str = 'logs',
    log_level: str = 'INFO'
) -> FlightLogger:
    """
    Get or create singleton FlightLogger instance.
    
    Args:
        name: Logger name
        log_dir: Directory for log files
        log_level: Logging level
    
    Returns:
        FlightLogger instance
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = FlightLogger(name, log_dir, log_level)
    return _logger_instance


if __name__ == '__main__':
    # Test logging
    logger = FlightLogger(log_level='DEBUG')
    
    logger.debug("This is a debug message")
    logger.info("System initialized")
    logger.warning("Low battery warning")
    logger.error("GPS signal lost")
    logger.critical("Emergency landing required")
    
    logger.log_telemetry({
        'altitude': 15.5,
        'speed': 3.2,
        'battery': 11.8,
        'gps_sats': 10
    })
    
    logger.log_mission_event('TAKEOFF', 'Target altitude: 10m')
    logger.log_safety_event('Geofence approached', 'WARNING')
    logger.log_connection_event('Connected to vehicle', 'udp:127.0.0.1:14550')
    
    print("\nTest completed. Check logs directory for output.")
