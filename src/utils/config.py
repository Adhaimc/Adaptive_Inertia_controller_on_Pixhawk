"""
Configuration management for Erle-Brain 2 autonomous flight system.
Handles loading and accessing configuration parameters from YAML files.
"""

import os
import yaml
from typing import Any, Dict


class Config:
    """Configuration manager for flight parameters."""
    
    def __init__(self, config_path: str = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to YAML configuration file
        """
        if config_path is None:
            # Default to config/flight_params.yaml
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            config_path = os.path.join(base_dir, 'config', 'flight_params.yaml')
        
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file.
        
        Returns:
            Dictionary containing configuration parameters
        """
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Warning: Config file not found at {self.config_path}")
            print("Using default configuration...")
            return self._get_default_config()
        except yaml.YAMLError as e:
            print(f"Error parsing YAML config: {e}")
            print("Using default configuration...")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration if file loading fails.
        
        Returns:
            Dictionary with default parameters
        """
        return {
            'connection': {
                'default_string': 'udp:127.0.0.1:14550',
                'baud_rate': 921600,
                'timeout': 30
            },
            'flight': {
                'min_altitude': 2.0,
                'max_altitude': 50.0,
                'default_altitude': 10.0,
                'min_speed': 0.5,
                'max_speed': 10.0,
                'default_speed': 5.0,
                'takeoff_altitude': 10.0,
                'takeoff_climb_rate': 1.0,
                'landing_descent_rate': 1.0,
                'landing_threshold_altitude': 0.3
            },
            'safety': {
                'battery_critical': 10.5,
                'battery_warning': 11.1,
                'battery_full': 12.6,
                'gps_min_satellites': 6,
                'gps_min_hdop': 2.0,
                'require_gps_lock': True,
                'require_home_set': True,
                'check_battery_level': True,
                'check_rc_connection': True
            },
            'geofence': {
                'enabled': True,
                'type': 'cylinder',
                'radius': 100.0,
                'min_altitude': 2.0,
                'max_altitude': 50.0,
                'breach_action': 'RTL'
            },
            'telemetry': {
                'position_rate': 10,
                'attitude_rate': 10,
                'battery_rate': 1,
                'gps_rate': 1,
                'enable_logging': True,
                'log_directory': 'logs',
                'log_level': 'INFO',
                'verbose': True
            }
        }
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation key path.
        
        Args:
            key_path: Dot-separated path to config value (e.g., 'flight.default_altitude')
            default: Default value if key not found
        
        Returns:
            Configuration value or default
        
        Example:
            >>> config = Config()
            >>> altitude = config.get('flight.default_altitude')
            >>> print(altitude)  # 10.0
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any) -> None:
        """
        Set configuration value by dot-notation key path.
        
        Args:
            key_path: Dot-separated path to config value
            value: New value to set
        """
        keys = key_path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def save(self, output_path: str = None) -> None:
        """
        Save current configuration to YAML file.
        
        Args:
            output_path: Path to save config (defaults to original path)
        """
        if output_path is None:
            output_path = self.config_path
        
        with open(output_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
    
    def reload(self) -> None:
        """Reload configuration from file."""
        self.config = self._load_config()
    
    def __repr__(self) -> str:
        return f"Config(path='{self.config_path}')"


# Singleton instance for easy access
_config_instance = None


def get_config(config_path: str = None) -> Config:
    """
    Get or create singleton Config instance.
    
    Args:
        config_path: Optional path to config file
    
    Returns:
        Config instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_path)
    return _config_instance


if __name__ == '__main__':
    # Test configuration loading
    config = Config()
    print("Configuration loaded successfully!")
    print(f"\nConnection string: {config.get('connection.default_string')}")
    print(f"Default altitude: {config.get('flight.default_altitude')} meters")
    print(f"Max speed: {config.get('flight.max_speed')} m/s")
    print(f"Battery critical: {config.get('safety.battery_critical')} V")
    print(f"Geofence radius: {config.get('geofence.radius')} meters")
    print(f"\nFull config: {config.config}")
