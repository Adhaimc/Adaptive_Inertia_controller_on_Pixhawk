# RC Override Controller - Quick Integration Guide

## Your Setup

You have **no RC receiver**, so you'll control the Pixhawk entirely via USB/serial using:
- **RC Override Controller** (new: `src/rc_override_controller.py`)
- Your **AIC Controller** (existing: `src/modules/attitude_controller_aic/`)

## Integration Steps

### Step 1: Test Basic RC Override (TODAY)

```bash
# 1. Find your USB port
ls /dev/cu.usb*
# Note the port, e.g., /dev/cu.usbmodem14101

# 2. Update config/flight_params.yaml with your port
# Edit the connection section:
# connection:
#   default_string: '/dev/cu.usbmodem14101'
#   baud_rate: 115200

# 3. Run the test script
python test_rc_override.py
```

Expected to see:
- ✓ Connected
- ✓ Vehicle info displayed
- ✓ Throttle ramps 0→50%
- ✓ Disarm successful

### Step 2: Integrate AIC Controller (TOMORROW)

Create a new file: `src/rc_aic_controller.py`

```python
"""
Combined RC Override + AIC Controller
Converts AIC torque commands to RC stick inputs
"""

from src.rc_override_controller import RCOverrideController, FlightMode
from src.modules.attitude_controller_aic.AttitudeControllerAIC import AttitudeControllerAIC
import numpy as np
import time


class RCAICController:
    """RC Override with AIC torque control."""
    
    def __init__(self, port='/dev/cu.usbmodem14101'):
        """Initialize RC + AIC controller."""
        self.rc = RCOverrideController(port)
        self.aic = AttitudeControllerAIC()
        
        # Torque limits (tune these for your quad)
        self.max_torque = np.array([0.5, 0.5, 0.3])  # τ_max per axis (Nm)
        self.max_rc = 50  # ±50% stick deflection
    
    def torque_to_rc(self, torque_cmd):
        """
        Convert AIC torque commands to RC stick inputs.
        
        Args:
            torque_cmd: [τ_roll, τ_pitch, τ_yaw] from AIC
            
        Returns:
            (roll_cmd%, pitch_cmd%, yaw_cmd%) for RC sticks
        """
        # Normalize by max torque
        normalized = torque_cmd / self.max_torque
        
        # Scale to RC range (±50%)
        rc_cmd = np.clip(normalized * self.max_rc, -self.max_rc, self.max_rc)
        
        return rc_cmd
    
    def control_loop(self, desired_attitude_rad, duration=10):
        """
        Main control loop combining RC override + AIC.
        
        Args:
            desired_attitude_rad: [roll, pitch, yaw] in radians
            duration: Loop duration in seconds
        """
        self.rc.connect()
        self.rc.set_mode(FlightMode.STABILIZE)
        self.rc.arm()
        self.rc.start_monitoring()
        
        try:
            # Set neutral throttle
            self.rc.set_throttle(45)  # Hover throttle
            
            start_time = time.time()
            while time.time() - start_time < duration:
                # Get current attitude from Pixhawk
                info = self.rc.get_vehicle_info()
                current_attitude = np.array([
                    info['attitude']['roll'],
                    info['attitude']['pitch'],
                    info['attitude']['yaw'],
                ])
                
                # Compute AIC torques
                # (You need to implement this based on your AIC module)
                torques = self.aic.compute_control(
                    desired_attitude_rad,
                    current_attitude,
                    angular_velocity=np.array([0, 0, 0]),  # Get from Pixhawk
                    inertia_estimate=np.eye(3) * 0.04,  # Your quad's inertia
                )
                
                # Convert to RC commands
                rc_cmd = self.torque_to_rc(torques)
                
                # Send to Pixhawk
                self.rc.set_attitude(rc_cmd[0], rc_cmd[1], rc_cmd[2])
                
                time.sleep(0.02)  # 50 Hz control loop
        
        finally:
            self.rc.neutral_sticks()
            self.rc.disarm()
            self.rc.disconnect()


if __name__ == '__main__':
    # Example: Hold level attitude (0, 0, 0) for 30 seconds
    controller = RCAICController('/dev/cu.usbmodem14101')
    
    desired_attitude = np.array([0, 0, 0])  # radians
    controller.control_loop(desired_attitude, duration=30)
```

### Step 3: Benchtop Testing (PROPS OFF)

```python
# Create test_aic_benchtop.py
from src.rc_aic_controller import RCAICController
import numpy as np

controller = RCAICController('/dev/cu.usbmodem14101')

# Test 1: Hover throttle response
print("Test 1: Hovering...")
controller.rc.connect()
controller.rc.set_mode(FlightMode.STABILIZE)
controller.rc.arm()

for throttle in [40, 45, 50, 45, 40]:
    print(f"Throttle: {throttle}%")
    controller.rc.set_throttle(throttle)
    time.sleep(2)

controller.rc.disarm()
controller.rc.disconnect()
```

### Step 4: First Flight (OUTDOORS)

```python
# Create flight_test_aic.py
from src.rc_aic_controller import RCAICController
import numpy as np

controller = RCAICController('/dev/cu.usbmodem14101')

# Hover for 30 seconds at level attitude
desired = np.array([0, 0, 0])  # radians = level, no rotation
controller.control_loop(desired, duration=30)
```

## Key Parameters to Tune

### 1. Torque Limits (`max_torque`)
```python
# Conservative start
self.max_torque = np.array([0.3, 0.3, 0.2])  # Nm

# More aggressive
self.max_torque = np.array([0.5, 0.5, 0.3])  # Nm
```

### 2. RC Stick Limit (`max_rc`)
```python
# Conservative (won't let stick go beyond ±50%)
self.max_rc = 50

# Aggressive (full stick up to ±100%)
self.max_rc = 100
```

### 3. Control Loop Rate
```python
# Current: 50 Hz (0.02s)
time.sleep(0.02)

# Higher rate: 100 Hz (better tracking)
time.sleep(0.01)

# Lower rate: 25 Hz (safety)
time.sleep(0.04)
```

## Testing Checklist

- [ ] **Day 1: USB Connection**
  - [ ] Run `test_rc_override.py` successfully
  - [ ] See vehicle info and throttle response
  - [ ] Battery voltage > 11V

- [ ] **Day 2: Benchtop (Props OFF)**
  - [ ] Arm/disarm works
  - [ ] Throttle commands register
  - [ ] Attitude readings stable
  - [ ] No jitter in RC values

- [ ] **Day 3: Tethered Hover**
  - [ ] Arm successfully
  - [ ] Gentle throttle ramp to hover
  - [ ] Stable hover for 10 seconds
  - [ ] Gentle stick input responds smoothly

- [ ] **Day 4: Free Flight**
  - [ ] Takeoff to 0.5m hover
  - [ ] Maintain altitude ±0.5m
  - [ ] Attitude error < 5°
  - [ ] Land smoothly
  - [ ] Download logs and review

## Common Issues & Fixes

### Throttle Not Responding
```python
# Check RC override is enabled
rc.vehicle.channels.overrides  # Should show {3: 1300, ...}

# Verify channel 3 (throttle) is being updated
rc.set_throttle(50)
print(rc.vehicle.channels.overrides)  # Should show 3: 1750
```

### Unstable Oscillations
```python
# Reduce max torque (less aggressive)
self.max_torque = np.array([0.3, 0.3, 0.15])

# Or reduce RC stick range
self.max_rc = 30  # Only ±30% stick
```

### Control Loop Too Slow
```python
# Increase update frequency
while ...:
    # Your control code
    time.sleep(0.01)  # 100 Hz instead of 50 Hz
```

## File Structure After Integration

```
src/
├── rc_override_controller.py      # Low-level RC control (NEW)
├── rc_aic_controller.py           # RC + AIC combined (NEW)
├── autonomous_flight.py           # Existing flight controller
├── mission_planner.py             # Existing mission planner
├── safety_manager.py              # Existing safety (can reuse)
├── telemetry_monitor.py           # Existing telemetry
└── modules/
    └── attitude_controller_aic/   # Your AIC controller
        ├── AttitudeControllerAIC.cpp
        └── include/
            ├── attitude_controller_aic.hpp
            ├── adaptive_estimator.hpp
            └── ...

tests/
├── test_rc_override.py            # RC override test (NEW)
├── test_aic_benchtop.py           # Benchtop AIC test (NEW)
└── test_flight_aic.py             # Flight test (NEW)
```

## Next Commands to Try

```bash
# 1. Test RC override
python test_rc_override.py

# 2. Once working, create integrated controller
# Create src/rc_aic_controller.py (template above)

# 3. Benchtop test
python tests/test_aic_benchtop.py

# 4. First flight (tethered)
python tests/test_flight_aic.py
```

---

**Ready to go!** Once the Pixhawk is physically connected via USB, start with `python test_rc_override.py` and follow the checklist above.
