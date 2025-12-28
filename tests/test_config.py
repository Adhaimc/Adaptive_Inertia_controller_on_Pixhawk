"""
Unit tests for configuration management.
"""

import unittest
import tempfile
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.config import Config


class TestConfig(unittest.TestCase):
    """Test cases for Config class."""
    
    def test_get_default_config(self):
        """Test loading default configuration."""
        config = Config()
        
        # Test getting values
        self.assertIsNotNone(config.get('connection.default_string'))
        self.assertIsNotNone(config.get('flight.default_altitude'))
        self.assertIsNotNone(config.get('safety.battery_critical'))
    
    def test_get_with_default(self):
        """Test get method with default value."""
        config = Config()
        
        # Non-existent key should return default
        value = config.get('nonexistent.key', 'default_value')
        self.assertEqual(value, 'default_value')
    
    def test_set_value(self):
        """Test setting configuration value."""
        config = Config()
        
        config.set('test.value', 123)
        self.assertEqual(config.get('test.value'), 123)
    
    def test_nested_get(self):
        """Test nested key access."""
        config = Config()
        
        altitude = config.get('flight.default_altitude')
        self.assertIsNotNone(altitude)
        self.assertIsInstance(altitude, (int, float))


if __name__ == '__main__':
    unittest.main()
