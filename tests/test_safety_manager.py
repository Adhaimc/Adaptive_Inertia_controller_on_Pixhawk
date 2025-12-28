"""
Unit tests for Safety Manager module.
"""

import unittest
from unittest.mock import Mock, MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from safety_manager import SafetyManager


class TestSafetyManager(unittest.TestCase):
    """Test cases for SafetyManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock vehicle
        self.mock_vehicle = Mock()
        
        # Mock GPS
        self.mock_vehicle.gps_0 = Mock()
        self.mock_vehicle.gps_0.fix_type = 3
        self.mock_vehicle.gps_0.satellites_visible = 10
        self.mock_vehicle.gps_0.eph = 100
        
        # Mock battery
        self.mock_vehicle.battery = Mock()
        self.mock_vehicle.battery.voltage = 12.0
        self.mock_vehicle.battery.level = 80
        
        # Mock home location
        self.mock_vehicle.home_location = Mock()
        self.mock_vehicle.home_location.lat = 37.7749
        self.mock_vehicle.home_location.lon = -122.4194
        
        # Mock sensors
        self.mock_vehicle.attitude = Mock()
        self.mock_vehicle.velocity = [0, 0, 0]
        
        # Mock RC
        self.mock_vehicle.channels = {'1': 1500}
        
        # Mock mode
        self.mock_vehicle.mode = Mock()
        self.mock_vehicle.mode.name = 'GUIDED'
        
        # Create safety manager
        self.safety = SafetyManager(self.mock_vehicle)
    
    def test_gps_lock_ok(self):
        """Test GPS lock check with good GPS."""
        success, message = self.safety.check_gps_lock()
        self.assertTrue(success)
        self.assertIn('GPS OK', message)
    
    def test_gps_lock_no_fix(self):
        """Test GPS lock check with no fix."""
        self.mock_vehicle.gps_0.fix_type = 0
        success, message = self.safety.check_gps_lock()
        self.assertFalse(success)
        self.assertIn('No GPS fix', message)
    
    def test_gps_lock_insufficient_satellites(self):
        """Test GPS lock check with insufficient satellites."""
        self.mock_vehicle.gps_0.satellites_visible = 4
        success, message = self.safety.check_gps_lock()
        self.assertFalse(success)
        self.assertIn('Insufficient satellites', message)
    
    def test_battery_ok(self):
        """Test battery check with good battery."""
        success, message = self.safety.check_battery()
        self.assertTrue(success)
        self.assertIn('Battery OK', message)
    
    def test_battery_critical(self):
        """Test battery check with critical battery."""
        self.mock_vehicle.battery.voltage = 10.0
        success, message = self.safety.check_battery()
        self.assertFalse(success)
        self.assertIn('critical', message.lower())
    
    def test_battery_warning(self):
        """Test battery check with low battery."""
        self.mock_vehicle.battery.voltage = 11.0
        success, message = self.safety.check_battery()
        self.assertTrue(success)
        self.assertIn('low but acceptable', message.lower())
    
    def test_home_position_ok(self):
        """Test home position check with valid home."""
        success, message = self.safety.check_home_position()
        self.assertTrue(success)
        self.assertIn('Home set', message)
    
    def test_home_position_not_set(self):
        """Test home position check with no home."""
        self.mock_vehicle.home_location = None
        success, message = self.safety.check_home_position()
        self.assertFalse(success)
        self.assertIn('not set', message)


if __name__ == '__main__':
    unittest.main()
