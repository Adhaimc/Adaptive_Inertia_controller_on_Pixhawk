"""
Mission Planner for Erle-Brain 2 autonomous flight system.
Handles mission loading, waypoint management, and mission execution.
"""

import json
import time
import math
from typing import List, Dict, Optional, Tuple
from dronekit import Vehicle, LocationGlobalRelative, Command
from pymavlink import mavutil

from utils.logger import get_logger
from utils.config import get_config


class MissionPlanner:
    """Manages mission planning and waypoint navigation."""
    
    def __init__(self, vehicle: Vehicle):
        """
        Initialize mission planner.
        
        Args:
            vehicle: Connected DroneKit vehicle instance
        """
        self.vehicle = vehicle
        self.config = get_config()
        self.logger = get_logger()
        
        self.current_mission: Optional[Dict] = None
        self.waypoints: List[LocationGlobalRelative] = []
        self.waypoint_radius = self.config.get('mission.waypoint_radius', 2.0)
    
    def load_mission_from_file(self, mission_file: str) -> bool:
        """
        Load mission from JSON file.
        
        Args:
            mission_file: Path to mission JSON file
        
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            with open(mission_file, 'r') as f:
                self.current_mission = json.load(f)
            
            self.logger.log_mission_event('Mission loaded', mission_file)
            self._parse_mission()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load mission: {str(e)}")
            return False
    
    def _parse_mission(self) -> None:
        """Parse mission data and extract waypoints."""
        if not self.current_mission:
            return
        
        self.waypoints = []
        waypoints_data = self.current_mission.get('waypoints', [])
        
        for wp in waypoints_data:
            location = LocationGlobalRelative(
                wp['lat'],
                wp['lon'],
                wp.get('alt', self.config.get('flight.default_altitude', 10.0))
            )
            self.waypoints.append(location)
        
        self.logger.info(f"Parsed {len(self.waypoints)} waypoints")
    
    def create_simple_mission(
        self,
        waypoints: List[Tuple[float, float, float]]
    ) -> None:
        """
        Create a simple mission from list of coordinates.
        
        Args:
            waypoints: List of (lat, lon, alt) tuples
        """
        self.waypoints = []
        
        for lat, lon, alt in waypoints:
            location = LocationGlobalRelative(lat, lon, alt)
            self.waypoints.append(location)
        
        self.current_mission = {
            'name': 'Custom Mission',
            'waypoints': [
                {'lat': wp.lat, 'lon': wp.lon, 'alt': wp.alt}
                for wp in self.waypoints
            ]
        }
        
        self.logger.log_mission_event('Custom mission created', f'{len(waypoints)} waypoints')
    
    def upload_mission_to_vehicle(self) -> bool:
        """
        Upload mission waypoints to vehicle.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            cmds = self.vehicle.commands
            cmds.clear()
            
            # Add home location (required)
            home = self.vehicle.home_location
            if home is None:
                self.logger.error("Home location not set")
                return False
            
            # Add takeoff command
            takeoff_alt = self.config.get('flight.takeoff_altitude', 10.0)
            cmds.add(Command(
                0, 0, 0,
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
                0, 0, 0, 0, 0, 0, 0, 0, takeoff_alt
            ))
            
            # Add waypoint commands
            for wp in self.waypoints:
                cmds.add(Command(
                    0, 0, 0,
                    mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                    mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
                    0, 0, 0, 0, 0, 0,
                    wp.lat, wp.lon, wp.alt
                ))
            
            # Add RTL command at end
            cmds.add(Command(
                0, 0, 0,
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH,
                0, 0, 0, 0, 0, 0, 0, 0, 0
            ))
            
            # Upload commands
            cmds.upload()
            self.logger.log_mission_event('Mission uploaded to vehicle', f'{len(self.waypoints)} waypoints')
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to upload mission: {str(e)}")
            return False
    
    def goto_waypoint(
        self,
        lat: float,
        lon: float,
        alt: float,
        groundspeed: Optional[float] = None
    ) -> None:
        """
        Command vehicle to go to specific waypoint.
        
        Args:
            lat: Latitude
            lon: Longitude
            alt: Altitude (meters, relative)
            groundspeed: Target groundspeed in m/s
        """
        location = LocationGlobalRelative(lat, lon, alt)
        
        self.logger.log_mission_event(
            'Going to waypoint',
            f'Lat: {lat:.6f}, Lon: {lon:.6f}, Alt: {alt:.1f}m'
        )
        
        # Set groundspeed if specified
        if groundspeed:
            self.set_groundspeed(groundspeed)
        
        self.vehicle.simple_goto(location)
    
    def goto_waypoint_location(
        self,
        location: LocationGlobalRelative,
        groundspeed: Optional[float] = None
    ) -> None:
        """
        Command vehicle to go to LocationGlobalRelative.
        
        Args:
            location: Target location
            groundspeed: Target groundspeed in m/s
        """
        self.goto_waypoint(location.lat, location.lon, location.alt, groundspeed)
    
    def wait_for_waypoint_reached(
        self,
        target_location: LocationGlobalRelative,
        timeout: int = 120
    ) -> bool:
        """
        Wait until vehicle reaches target waypoint.
        
        Args:
            target_location: Target waypoint location
            timeout: Maximum wait time in seconds
        
        Returns:
            True if reached, False if timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            current_location = self.vehicle.location.global_relative_frame
            distance = self._get_distance_to_location(current_location, target_location)
            
            self.logger.debug(f"Distance to waypoint: {distance:.2f}m")
            
            if distance < self.waypoint_radius:
                self.logger.log_mission_event('Waypoint reached')
                return True
            
            time.sleep(0.5)
        
        self.logger.log_safety_event(
            f'Waypoint not reached within {timeout}s',
            'WARNING'
        )
        return False
    
    def execute_waypoint_mission(
        self,
        waypoints: Optional[List[Tuple[float, float, float]]] = None,
        groundspeed: Optional[float] = None
    ) -> bool:
        """
        Execute waypoint mission sequentially.
        
        Args:
            waypoints: Optional list of (lat, lon, alt) tuples
            groundspeed: Target groundspeed in m/s
        
        Returns:
            True if mission completed, False otherwise
        """
        if waypoints:
            self.create_simple_mission(waypoints)
        
        if not self.waypoints:
            self.logger.error("No waypoints to execute")
            return False
        
        self.logger.log_mission_event('Starting waypoint mission', f'{len(self.waypoints)} waypoints')
        
        # Set groundspeed if specified
        if groundspeed:
            self.set_groundspeed(groundspeed)
        
        # Execute each waypoint
        for i, wp in enumerate(self.waypoints, 1):
            self.logger.log_mission_event(
                f'Waypoint {i}/{len(self.waypoints)}',
                f'Lat: {wp.lat:.6f}, Lon: {wp.lon:.6f}, Alt: {wp.alt:.1f}m'
            )
            
            self.vehicle.simple_goto(wp)
            
            if not self.wait_for_waypoint_reached(wp):
                self.logger.error(f"Failed to reach waypoint {i}")
                return False
        
        self.logger.log_mission_event('Mission completed successfully')
        return True
    
    def set_groundspeed(self, speed: float) -> None:
        """
        Set vehicle groundspeed.
        
        Args:
            speed: Groundspeed in m/s
        """
        max_speed = self.config.get('flight.max_speed', 10.0)
        min_speed = self.config.get('flight.min_speed', 0.5)
        
        # Clamp speed to limits
        speed = max(min_speed, min(speed, max_speed))
        
        self.vehicle.groundspeed = speed
        self.logger.info(f"Groundspeed set to {speed:.1f} m/s")
    
    def _get_distance_to_location(
        self,
        location1: LocationGlobalRelative,
        location2: LocationGlobalRelative
    ) -> float:
        """
        Calculate distance between two locations in meters.
        
        Args:
            location1: First location
            location2: Second location
        
        Returns:
            Distance in meters
        """
        dlat = location2.lat - location1.lat
        dlon = location2.lon - location1.lon
        dalt = location2.alt - location1.alt
        
        # Approximate distance calculation
        lat_distance = dlat * 111320  # meters per degree latitude
        lon_distance = dlon * 111320 * math.cos(math.radians(location1.lat))
        
        horizontal_distance = math.sqrt(lat_distance**2 + lon_distance**2)
        total_distance = math.sqrt(horizontal_distance**2 + dalt**2)
        
        return total_distance
    
    def get_current_mission_info(self) -> Dict:
        """
        Get information about current mission.
        
        Returns:
            Dictionary with mission information
        """
        if not self.current_mission:
            return {'status': 'No mission loaded'}
        
        return {
            'name': self.current_mission.get('name', 'Unknown'),
            'waypoint_count': len(self.waypoints),
            'waypoints': [
                {'lat': wp.lat, 'lon': wp.lon, 'alt': wp.alt}
                for wp in self.waypoints
            ]
        }


if __name__ == '__main__':
    print("Mission Planner module - use with autonomous_flight.py")
