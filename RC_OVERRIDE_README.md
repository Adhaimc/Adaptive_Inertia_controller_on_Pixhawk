# RC Override Controller for Pixhawk (No RC Receiver Required)

This module provides serial-based control of your Pixhawk without an RC transmitter. Perfect for:
- Testing and development
- Implementing custom control algorithms
- Autonomous flight systems
- Your AIC (Adaptive Inertia Controller) implementation

## Quick Start

### 1. Find Your USB Port

**macOS:**
```bash
ls /dev/cu.usb*
# Output example: /dev/cu.usbmodem14101
```

**Linux:**
```bash
ls /dev/ttyUSB*
# Output example: /dev/ttyUSB0
```

### 2. Update Configuration

Edit `config/flight_params.yaml`:
```yaml
connection:
  default_string: '/dev/cu.usbmodem14101'  # YOUR PORT
  baud_rate: 115200                         # Must be 115200 for USB
```

### 3. Test Connection

```bash
cd /Users/adhaimc/Documents/GitHub/Erle_brain2

# Run the test script
python test_rc_override.py
```

Expected output:
```
[1] Connecting to Pixhawk...
✓ Connected
[2] Getting vehicle info...
  Mode: STABILIZE
  Armed: False
  Armable: True
  Battery: 12.4V
  Attitude: R=0.0° P=0.0° Y=0.0°
...
✓ TEST COMPLETE
```

## Usage Examples

### Basic Control (Interactive Mode)

```bash
python -m src.rc_override_controller --port /dev/cu.usbmodem14101
```

Commands:
```
>> arm                    # Arm vehicle
>> mode STABILIZE        # Set flight mode
>> throttle 50           # Set throttle to 50%
>> neutral               # Center all sticks
>> disarm                # Disarm vehicle
>> info                  # Show vehicle status
>> exit                  # Exit program
```

### Python Script Integration

```python
from src.rc_override_controller import RCOverrideController, FlightMode
import time

# Create controller
controller = RCOverrideController('/dev/cu.usbmodem14101')

# Connect
controller.connect()
controller.start_monitoring()

# Arm and test
controller.set_mode(FlightMode.STABILIZE)
controller.arm()

# Set throttle
controller.set_throttle(50)  # 50%
time.sleep(5)

# Set attitude
controller.set_attitude(roll=10, pitch=5, yaw=0)
time.sleep(5)

# Disarm
controller.disarm()
controller.disconnect()
```

### With Your AIC Controller

```python
from src.rc_override_controller import RCOverrideController, FlightMode
from src.modules.attitude_controller_aic import AttitudeControllerAIC
import numpy as np

controller = RCOverrideController('/dev/cu.usbmodem14101')
controller.connect()
controller.arm()

aic = AttitudeControllerAIC()

# Control loop
while controller.vehicle.armed:
    # Get desired attitude (e.g., from path planning)
    desired_attitude = [0, 0, 0]  # roll, pitch, yaw
    
    # Your AIC controller computes torques
    torques = aic.compute_control(desired_attitude)
    
    # Convert torques to RC commands (implement this)
    roll_cmd = convert_torque_to_rc(torques[0])
    pitch_cmd = convert_torque_to_rc(torques[1])
    yaw_cmd = convert_torque_to_rc(torques[2])
    
    controller.set_attitude(roll_cmd, pitch_cmd, yaw_cmd)
```

## API Reference

### Main Methods

#### Connection
- `connect()` → bool - Connect to Pixhawk
- `disconnect()` → None - Disconnect cleanly

#### Control
- `arm(timeout=10)` → bool - Arm motors
- `disarm(timeout=5)` → bool - Disarm motors
- `set_mode(mode: FlightMode, timeout=5)` → bool - Change flight mode

#### RC Channel Control
- `set_rc_channel(channel: int, pwm: int)` → None - Set single channel (1-8)
- `set_rc_channels(channels: Dict[int, int])` → None - Set multiple channels
- `set_throttle(percent: float)` → None - Set throttle 0-100%
- `set_attitude(roll: float, pitch: float, yaw: float)` → None - Set stick positions

#### Status
- `neutral_sticks()` → None - Center all sticks
- `start_monitoring()` → None - Log vehicle status
- `stop_monitoring()` → None - Stop status logging
- `get_vehicle_info()` → Dict - Get current vehicle state
- `test_hover(duration: float, throttle_percent: float)` → bool - Test hover

### RC Channel Mapping

| Channel | Function | Range |
|---------|----------|-------|
| 1 | Roll | 1000-2000 PWM (-100 to +100%) |
| 2 | Pitch | 1000-2000 PWM (-100 to +100%) |
| 3 | Throttle | 1000-2000 PWM (0-100%) |
| 4 | Yaw | 1000-2000 PWM (-100 to +100%) |
| 5-8 | Auxiliary | For future features |

PWM ranges:
- **Neutral (sticks centered):** 1500 PWM
- **Min (stick full down/back):** 1000 PWM
- **Max (stick full up/forward):** 2000 PWM

## Safety Features

✅ **RC Failsafe Disabled** - Automatically disabled since you have no RC receiver

✅ **Armability Check** - Won't arm if GPS/compass/battery issues detected

✅ **Altitude Monitoring** - Logs relative altitude in real-time

✅ **Battery Monitoring** - Warns if voltage drops too low

⚠️ **Manual Control Loss** - You must control via serial; if connection drops, quad will fall

## Troubleshooting

### Can't Connect
```bash
# 1. Check USB cable and port
ls /dev/cu.usb*

# 2. Test with MAVProxy
pip install MAVProxy pymavlink
mavproxy.py --master=/dev/cu.usbmodem14101 --baudrate=115200

# 3. Check Pixhawk LED (should be green/blue)
```

### Won't Arm
Check these in order:
1. **GPS:** Need 6+ satellites (green light in HUD)
2. **Compass:** Not being interfered with (no metal nearby)
3. **Accelerometer:** Placed level on flat surface
4. **Battery:** > 11V for 3S LiPo
5. **Mode:** Must be STABILIZE, ACRO, or GUIDED for arming

```python
# Debug armability
controller.connect()
info = controller.get_vehicle_info()
print(f"Armable: {info['is_armable']}")
print(f"Mode: {info['mode']}")
print(f"Battery: {info['battery']['voltage']}V")
print(f"Attitude: {info['attitude']}")
```

### Throttle Not Responding
1. Verify channel 3 is being set: `controller.set_throttle(50)`
2. Check ArduCopter throttle failsafe: `FS_THR_ENABLE = 0`
3. Verify mode is STABILIZE (need to test hover)

### Jerky/Unstable Movements
1. Reduce control gains in your algorithm
2. Check if attitude readings are noisy
3. Ensure Pixhawk not vibrating (use dampers)

## Advanced: Implementing Your AIC Controller

The RC Override Controller is a low-level interface. To use your AIC controller:

1. **Compute desired attitude:** From path planning or setpoints
2. **Run AIC:** Get torque commands τ = [τ_roll, τ_pitch, τ_yaw]
3. **Convert to RC:** Torques → attitude stick positions
4. **Send RC:** Update Pixhawk via `set_attitude()`

Example torque-to-RC conversion (implement based on your dynamics):

```python
def torque_to_rc(tau, max_torque=0.5):
    """
    Convert control torque to RC stick command.
    tau: desired torque (Nm)
    max_torque: max torque your motors can produce (Nm)
    """
    # Normalize to -100 to +100 (% of max stick deflection)
    rc_cmd = (tau / max_torque) * 100
    return max(-100, min(100, rc_cmd))
```

## Flight Modes Supported

All ArduCopter modes work, but for manual RC override control these are recommended:

| Mode | Use Case |
|------|----------|
| **STABILIZE** | Manual control with auto-leveling (best for testing) |
| **ACRO** | Full manual (advanced, no leveling) |
| **ALT_HOLD** | Maintains altitude, you control pitch/roll/yaw |
| **GUIDED** | For programmable waypoints |
| **LAND** | Auto-landing sequence |
| **RTL** | Return to launch (if GPS locked) |

## Next Steps

1. ✅ **Test basic control** - Run `test_rc_override.py`
2. ✅ **Implement torque conversion** - Integrate with your AIC
3. ✅ **Benchtop testing** - Props off, test RC commands
4. ✅ **Tethered flight** - Test with props at low throttle
5. ✅ **Free flight** - Start with 1m hover test

## Files

- `src/rc_override_controller.py` - Main controller class
- `test_rc_override.py` - Test script
- `config/flight_params.yaml` - Configuration (update USB port here)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review `IMPLEMENTATION_GUIDE_AIC.md` for control integration
3. See `PIXHAWK_QUICK_START.md` for hardware setup

---

**Happy flying!** ✈️
