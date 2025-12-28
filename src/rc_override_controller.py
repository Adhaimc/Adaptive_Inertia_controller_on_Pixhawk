"""
RC Override Controller for Pixhawk without Radio Receiver.
Simulates RC stick inputs via MAVLink RC channel override.

Useful for:
- Testing without RC transmitter
- Implementing custom control algorithms
- Autonomous flight with serial-based control
"""

import time
import threading
from typing import Optional, Dict, Tuple
from dronekit import Vehicle, VehicleMode
from enum import Enum

from utils.connection import VehicleConnection
from utils.logger import get_logger
from utils.config import get_config


class FlightMode(Enum):
    """ArduCopter flight modes."""
    STABILIZE = 0
    ACRO = 1
    ALT_HOLD = 2
    AUTO = 3
    GUIDED = 4
    LOITER = 5
    RTL = 6
    CIRCLE = 7
    LAND = 9
    DRIFT = 11
    SPORT = 13
    POSHOLD = 14
    BRAKE = 17
    THROW = 18


class RCOverrideController:
    """Control Pixhawk via RC channel overrides (no RC transmitter needed)."""
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize RC Override Controller.
        
        Args:
            connection_string: MAVLink connection string (e.g., '/dev/cu.usbmodem14101')
        """
        self.config = get_config()
        self.logger = get_logger()
        
        self.conn = VehicleConnection(connection_string)
        self.vehicle: Optional[Vehicle] = None
        
        # RC Channel ranges (PWM in microseconds)
        self.MIN_PWM = 1000
        self.MID_PWM = 1500
        self.MAX_PWM = 2000
        
        # Monitoring
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        self.logger.info("=" * 70)
        self.logger.info("RC OVERRIDE CONTROLLER FOR PIXHAWK (NO RC RECEIVER)")
        self.logger.info("=" * 70)
    
    def connect(self) -> bool:
        """
        Connect to Pixhawk.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.vehicle = self.conn.connect()
            if not self.vehicle:
                return False
            
            self.logger.info("Connected to Pixhawk")
            self.logger.info(f"Autopilot: {self.vehicle.system_status.state}")
            
            # Disable RC failsafe since we have no RC receiver
            self._configure_rc_failsafe()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Connection failed: {str(e)}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from vehicle."""
        self.stop_monitoring()
        self.conn.disconnect()
        self.logger.info("Disconnected from Pixhawk")
    
    def _configure_rc_failsafe(self) -> None:
        """Disable RC failsafe since we have no RC receiver."""
        try:
            # FS_THR_ENABLE: 0 = disabled, 1 = enabled
            self.vehicle.parameters['FS_THR_ENABLE'] = 0
            self.logger.info("RC failsafe disabled")
        except Exception as e:
            self.logger.warning(f"Could not set RC failsafe: {str(e)}")
    
    def set_rc_channel(self, channel: int, pwm: int) -> None:
        """
        Set a single RC channel.
        
        Args:
            channel: Channel number (1-8)
            pwm: PWM value (1000-2000 microseconds)
        """
        pwm = max(self.MIN_PWM, min(self.MAX_PWM, pwm))
        self.vehicle.channels.overrides[str(channel)] = pwm
    
    def set_rc_channels(self, channels: Dict[int, int]) -> None:
        """
        Set multiple RC channels at once.
        
        Args:
            channels: Dict of {channel: pwm_value}
                Channel 1: Roll
                Channel 2: Pitch
                Channel 3: Throttle
                Channel 4: Yaw
        """
        for channel, pwm in channels.items():
            self.set_rc_channel(channel, pwm)
    
    def arm(self, timeout: int = 10) -> bool:
        """
        Arm the vehicle.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("Arming vehicle...")
            
            # Check if armable
            if not self.vehicle.is_armable:
                self.logger.error("Vehicle not armable (check GPS, compass, accelerometer)")
                return False
            
            self.vehicle.armed = True
            
            # Wait for arm
            start_time = time.time()
            while not self.vehicle.armed:
                if time.time() - start_time > timeout:
                    self.logger.error(f"Arming timeout after {timeout}s")
                    return False
                time.sleep(0.1)
            
            self.logger.info("✓ Vehicle armed")
            return True
            
        except Exception as e:
            self.logger.error(f"Arm failed: {str(e)}")
            return False
    
    def disarm(self, timeout: int = 5) -> bool:
        """
        Disarm the vehicle.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("Disarming vehicle...")
            
            self.vehicle.armed = False
            
            # Wait for disarm
            start_time = time.time()
            while self.vehicle.armed:
                if time.time() - start_time > timeout:
                    self.logger.error(f"Disarm timeout after {timeout}s")
                    return False
                time.sleep(0.1)
            
            self.logger.info("✓ Vehicle disarmed")
            return True
            
        except Exception as e:
            self.logger.error(f"Disarm failed: {str(e)}")
            return False
    
    def set_mode(self, mode: FlightMode, timeout: int = 5) -> bool:
        """
        Set flight mode.
        
        Args:
            mode: FlightMode enum value
            timeout: Timeout in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Setting mode to {mode.name}...")
            
            self.vehicle.mode = VehicleMode(mode.name)
            
            # Wait for mode change
            start_time = time.time()
            while self.vehicle.mode.name != mode.name:
                if time.time() - start_time > timeout:
                    self.logger.error(f"Mode change timeout")
                    return False
                time.sleep(0.1)
            
            self.logger.info(f"✓ Mode set to {mode.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Mode change failed: {str(e)}")
            return False
    
    def neutral_sticks(self) -> None:
        """Set all sticks to neutral (center) position."""
        self.set_rc_channels({
            1: self.MID_PWM,  # Roll (center)
            2: self.MID_PWM,  # Pitch (center)
            3: self.MIN_PWM,  # Throttle (off)
            4: self.MID_PWM,  # Yaw (center)
        })
        self.logger.info("RC sticks set to neutral")
    
    def set_throttle(self, percent: float) -> None:
        """
        Set throttle percentage (0-100%).
        
        Args:
            percent: Throttle percentage (0=min, 100=max)
        """
        percent = max(0, min(100, percent))
        pwm = int(self.MIN_PWM + (self.MAX_PWM - self.MIN_PWM) * percent / 100)
        self.set_rc_channel(3, pwm)
    
    def set_attitude(self, roll: float = 0, pitch: float = 0, yaw: float = 0) -> None:
        """
        Set attitude (simplified - doesn't account for actual control curves).
        
        Args:
            roll: Roll stick deflection (-100 to 100, negative=left, positive=right)
            pitch: Pitch stick deflection (-100 to 100, negative=back, positive=forward)
            yaw: Yaw stick deflection (-100 to 100, negative=left, positive=right)
        """
        roll = max(-100, min(100, roll))
        pitch = max(-100, min(100, pitch))
        yaw = max(-100, min(100, yaw))
        
        roll_pwm = int(self.MID_PWM + roll * (self.MAX_PWM - self.MID_PWM) / 100)
        pitch_pwm = int(self.MID_PWM + pitch * (self.MAX_PWM - self.MID_PWM) / 100)
        yaw_pwm = int(self.MID_PWM + yaw * (self.MAX_PWM - self.MID_PWM) / 100)
        
        self.set_rc_channels({
            1: roll_pwm,
            2: pitch_pwm,
            4: yaw_pwm,
        })
    
    def start_monitoring(self) -> None:
        """Start monitoring vehicle status."""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_vehicle, daemon=True)
        self.monitor_thread.start()
        self.logger.info("Status monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop monitoring vehicle status."""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        self.logger.info("Status monitoring stopped")
    
    def _monitor_vehicle(self) -> None:
        """Monitor vehicle status periodically."""
        while self.is_monitoring:
            try:
                # Log status every 2 seconds
                self.logger.info(
                    f"Mode: {self.vehicle.mode.name} | "
                    f"Armed: {self.vehicle.armed} | "
                    f"Altitude: {self.vehicle.location.global_relative_frame.alt:.1f}m | "
                    f"Battery: {self.vehicle.battery.voltage:.1f}V"
                )
                time.sleep(2)
            except Exception as e:
                self.logger.debug(f"Monitor error: {str(e)}")
                break
    
    def calibrate_compass(self) -> bool:
        """
        Initiate compass calibration (requires GUI or external command).
        
        Returns:
            True if command sent successfully
        """
        try:
            self.logger.warning("Compass calibration requires Mission Planner GUI")
            self.logger.warning("Use Mission Planner → Initial Setup → Compass")
            return False
        except Exception as e:
            self.logger.error(f"Calibration failed: {str(e)}")
            return False
    
    def test_hover(self, duration: float = 10, throttle_percent: float = 50) -> bool:
        """
        Test hover by holding throttle for duration.
        
        Args:
            duration: Duration in seconds
            throttle_percent: Throttle percentage
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.vehicle.armed:
                self.logger.error("Vehicle must be armed first")
                return False
            
            self.logger.info(f"Testing hover for {duration}s at {throttle_percent}% throttle")
            
            start_time = time.time()
            while time.time() - start_time < duration:
                self.set_throttle(throttle_percent)
                time.sleep(0.1)
            
            # Return to neutral
            self.neutral_sticks()
            self.logger.info("Hover test complete")
            return True
            
        except Exception as e:
            self.logger.error(f"Hover test failed: {str(e)}")
            return False
    
    def get_vehicle_info(self) -> Dict:
        """
        Get current vehicle information.
        
        Returns:
            Dictionary with vehicle status
        """
        try:
            return {
                'mode': self.vehicle.mode.name,
                'armed': self.vehicle.armed,
                'is_armable': self.vehicle.is_armable,
                'location': {
                    'lat': self.vehicle.location.global_frame.lat,
                    'lon': self.vehicle.location.global_frame.lon,
                    'alt': self.vehicle.location.global_relative_frame.alt,
                },
                'attitude': {
                    'roll': self.vehicle.attitude.roll,
                    'pitch': self.vehicle.attitude.pitch,
                    'yaw': self.vehicle.attitude.yaw,
                },
                'velocity': {
                    'vx': self.vehicle.velocity[0],
                    'vy': self.vehicle.velocity[1],
                    'vz': self.vehicle.velocity[2],
                },
                'battery': {
                    'voltage': self.vehicle.battery.voltage,
                    'current': self.vehicle.battery.current,
                    'level': self.vehicle.battery.level,
                },
                'heading': self.vehicle.heading,
                'groundspeed': self.vehicle.groundspeed,
            }
        except Exception as e:
            self.logger.error(f"Failed to get vehicle info: {str(e)}")
            return {}


# ============================================================================
# Example Usage
# ============================================================================

def main():
    """Example: Connect and perform basic operations."""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='RC Override Controller for Pixhawk')
    parser.add_argument('--port', default='/dev/cu.usbmodem14101', help='USB port')
    parser.add_argument('--baud', type=int, default=115200, help='Baud rate')
    parser.add_argument('--test', action='store_true', help='Run test sequence')
    args = parser.parse_args()
    
    # Create controller
    controller = RCOverrideController(f"{args.port}")
    
    try:
        # Connect
        if not controller.connect():
            return
        
        # Start monitoring
        controller.start_monitoring()
        
        if args.test:
            # Test sequence
            print("\n" + "=" * 70)
            print("TEST SEQUENCE")
            print("=" * 70)
            
            # Set to STABILIZE mode
            if not controller.set_mode(FlightMode.STABILIZE):
                return
            
            time.sleep(1)
            
            # Arm
            if not controller.arm():
                return
            
            time.sleep(1)
            
            # Test hover
            print("\nTesting 10-second hover at 50% throttle...")
            controller.test_hover(duration=10, throttle_percent=50)
            
            time.sleep(1)
            
            # Disarm
            if not controller.disarm():
                return
            
            print("\n✓ Test sequence complete!")
        
        else:
            # Interactive mode
            print("\nInteractive Mode - Available Commands:")
            print("  arm              - Arm vehicle")
            print("  disarm           - Disarm vehicle")
            print("  mode STABILIZE   - Set flight mode")
            print("  throttle 50      - Set throttle to 50%")
            print("  neutral          - Set sticks to neutral")
            print("  attitude 10 0 0  - Set roll 10%, pitch 0%, yaw 0%")
            print("  info             - Print vehicle info")
            print("  exit             - Exit program")
            print()
            
            while True:
                try:
                    cmd = input(">> ").strip().lower()
                    
                    if cmd == 'exit':
                        break
                    elif cmd == 'arm':
                        controller.arm()
                    elif cmd == 'disarm':
                        controller.disarm()
                    elif cmd == 'neutral':
                        controller.neutral_sticks()
                    elif cmd == 'info':
                        info = controller.get_vehicle_info()
                        for key, val in info.items():
                            print(f"  {key}: {val}")
                    elif cmd.startswith('mode '):
                        mode_name = cmd.split()[1].upper()
                        try:
                            mode = FlightMode[mode_name]
                            controller.set_mode(mode)
                        except KeyError:
                            print(f"Unknown mode: {mode_name}")
                    elif cmd.startswith('throttle '):
                        percent = float(cmd.split()[1])
                        controller.set_throttle(percent)
                    elif cmd.startswith('attitude '):
                        parts = cmd.split()
                        roll = float(parts[1])
                        pitch = float(parts[2]) if len(parts) > 2 else 0
                        yaw = float(parts[3]) if len(parts) > 3 else 0
                        controller.set_attitude(roll, pitch, yaw)
                    else:
                        print("Unknown command")
                        
                except KeyboardInterrupt:
                    print("\nExiting...")
                    break
                except Exception as e:
                    print(f"Error: {str(e)}")
    
    finally:
        controller.disconnect()


if __name__ == '__main__':
    main()
