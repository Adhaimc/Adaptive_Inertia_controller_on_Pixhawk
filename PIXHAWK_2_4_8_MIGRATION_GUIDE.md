# Erlebrain 2 → Pixhawk 2.4.8 Migration Guide

## Overview

Migrating from Erle-Brain 2 to Pixhawk 2.4.8 involves:
- **Hardware swap** (different connectors, sensors, power distribution)
- **Firmware change** (ArduPilot firmware compilation/setup)
- **Python/DroneKit compatibility** (still uses MAVLink, minimal changes)
- **AIC controller adaptation** (PX4 vs ArduPilot differences)
- **Testing & tuning** (new hardware requires re-calibration)

---

## Phase 1: Hardware Preparation (1-2 hours)

### 1.1 Gather Hardware Components

**Essential:**
- Pixhawk 2.4.8 flight controller
- Pixhawk PMB (Power Management Board) or equivalent power module
- Micro SD card (16GB, class 10+)
- USB cable (A-Micro B for Pixhawk)
- Jumpers and servo extension cables

**Sensors (verify compatibility):**
- GPS/Compass module (likely reusable from Erlebrain if u-blox compatible)
- Compass calibration tools
- IMU calibration items

**Frame modifications:**
- Vibration dampers/isolators
- Mounting bracket for Pixhawk (smaller than Erlebrain)
- Servo connector adapters if needed

### 1.2 Physical Installation

| Step | Details |
|------|---------|
| **1. Remove Erlebrain 2** | Desolder/disconnect all connections |
| **2. Mount Pixhawk 2.4.8** | Use vibration dampers, orient with arrow forward |
| **3. Connect Motors** | Pixhawk uses Pixhawk servo outputs (channels 1-4 for quad) |
| **4. Connect ESCs** | Signal lines to outputs 1-4; power from battery |
| **5. Connect Power** | Use PMB to distribute battery power safely |
| **6. Connect RC Receiver** | PPM or SBUS to RC IN connector |
| **7. Connect GPS/Compass** | To GPS connector with correct orientation |
| **8. Connect Telemetry** | TELEM1/TELEM2 port (3DR radio or WiFi) |
| **9. Add Micro SD** | For logging and firmware storage |
| **10. Secure cables** | Use zipties, avoid motor noise coupling to IMU |

### 1.3 Pixhawk 2.4.8 Connector Pinout Reference

```
MAIN OUT (Motors/Servos):
  1 = Roll (Aileron / Front-Right Motor on Quad X)
  2 = Pitch (Elevator / Front-Left Motor on Quad X)
  3 = Throttle (Main throttle / Rear-Left Motor on Quad X)
  4 = Yaw (Rudder / Rear-Right Motor on Quad X)
  
Quadcopter X Configuration:
  Output 1: FR (Front Right)
  Output 2: FL (Front Left) 
  Output 3: RL (Rear Left)
  Output 4: RR (Rear Right)

Power Input:
  - 5V rail (max 2A) for autopilot, radios, sensors
  - Main battery (2S-6S LiPo) via PMB

SERIAL Connections:
  TELEM1 = Main telemetry (usually WiFi or 3DR radio)
  TELEM2 = Secondary (compass/external mag, i2c adapter)
  
GPIO/Analog:
  6 analog inputs (battery voltage/current, airspeed, etc.)
```

---

## Phase 2: Firmware & Software Setup (2-3 hours)

### 2.1 Firmware Selection

**Choose ONE:**

| Option | When to Use | Pros | Cons |
|--------|------------|------|------|
| **ArduCopter** | Staying with ArduPilot | Familiar, proven, supports custom modules | More steps to compile AIC module |
| **PX4** | Cleaner architecture | Native AIC module support, better modularity | Different parameter naming, new learning curve |

**Recommendation:** Continue with **ArduCopter 4.4.x** (same ecosystem as Erlebrain) for minimal disruption.

### 2.2 Install ArduCopter Firmware

#### Option A: Pre-built Firmware (Easiest)

```bash
# 1. Download Mission Planner (Windows) or MAVProxy (Mac/Linux)
# Mac: brew install mavproxy

# 2. Connect Pixhawk via USB
# 3. In Mission Planner: Initial Setup → Install Firmware → Copter 4.4.2
# 4. Restart autopilot
```

#### Option B: Compile Custom ArduCopter with AIC Module (Advanced)

```bash
# Clone ArduPilot
git clone https://github.com/ArduPilot/ardupilot.git
cd ardupilot
git checkout Copter-4.4.2  # Or latest 4.4.x

# Copy your AIC module
cp -r /path/to/your/AIC/module ./modules/attitude_controller_aic/

# Update CMakeLists.txt to include AIC
# (See Phase 3.1 below)

# Build for Pixhawk
./waf configure --board pixhawk
./waf copter
./waf copter --upload  # If connected via USB
```

### 2.3 Ground Station Setup

Install on your **ground computer** (not Pixhawk):

```bash
# Option 1: Mission Planner (Windows/MacOS via Parallels)
# Download from: http://firmware.ardupilot.org

# Option 2: QGroundControl (All platforms)
brew install qgroundcontrol  # macOS

# Option 3: MAVProxy (Command line, all platforms)
pip install MAVProxy

# Keep DroneKit setup for Python autonomy:
pip install dronekit pymavlink pyyaml
```

### 2.4 Connection String Changes

Update your `flight_params.yaml`:

```yaml
connection:
  # For Pixhawk 2.4.8 (change from Erlebrain defaults):
  # Option 1: Serial (USB connected to ground computer)
  default_string: '/dev/ttyUSB0'  # Linux
  default_string: '/dev/cu.usbmodem14101'  # macOS
  baud_rate: 115200  # Pixhawk uses 115200, NOT 921600
  
  # Option 2: Telemetry Radio (3DR or equivalent)
  default_string: '/dev/ttyUSB0'
  baud_rate: 57600
  
  # Option 3: WiFi (if using WiFi module on TELEM2)
  default_string: 'udp:192.168.1.100:14550'  # AP IP:port
  timeout: 30
```

---

## Phase 3: Code Migration (2-3 hours)

### 3.1 AIC Module Adaptation

The core control algorithms work on **any** ArduPilot-based system. Required changes:

#### A. Update CMakeLists.txt (if compiling)

**File:** `src/modules/attitude_controller_aic/CMakeLists.txt`

```cmake
# For ArduPilot (no changes - already works)
# For PX4 (different build system):
# - Switch to PX4 Firmware build system
# - Add to src/modules/attitude_controller_aic/module.yaml
```

#### B. Pin Configuration (if hardcoded)

**File:** `src/modules/attitude_controller_aic/AttitudeControllerAIC.cpp`

Check if any motor output pins are hardcoded. Pixhawk 2.4.8 uses:
- Output 1: Roll
- Output 2: Pitch  
- Output 3: Throttle
- Output 4: Yaw

Most ArduCopter code is abstract and handles this automatically. **No changes needed** unless you see hardcoded servo pin numbers.

#### C. Sensor Interface Changes

Check `iwg_adapter.hpp` for any Erlebrain-specific sensor reading code:

```cpp
// WRONG (Erlebrain-specific):
// imu_data = erlebrain.read_imu_directly();

// CORRECT (ArduPilot abstraction):
// imu_data comes via MAVLink IMU messages
// OR via autopilot's internal sensor interface
```

### 3.2 Python Code Changes (Minimal)

Your DroneKit code is **hardware-agnostic**. Only update connection parameters:

**File:** `src/utils/connection.py`

```python
# Already handles multiple connection strings ✓
# Just update config values in flight_params.yaml

# Verify these work:
# ✓ connect() function (uses DroneKit, works with any MAVLink device)
# ✓ Vehicle mode changes (same MAVLink commands)
# ✓ Telemetry reading (same MAVLink messages)
```

### 3.3 Parameter Tuning File

Your current `flight_params.yaml` needs **parameter adjustments** for Pixhawk 2.4.8:

**File:** `config/flight_params.yaml`

Add new section or modify existing:

```yaml
# Pixhawk 2.4.8 Specific Parameters

pixhawk:
  # Motor placement (X config for quad)
  motor_layout: "QUAD_X"  # or QUAD_PLUS
  
  # Compass declination (location-dependent, degrees)
  compass_declination: 5.2  # Update for your location
  
  # Accelerometer/Gyro calibration data
  # (will be set during initial setup wizard)
  
flight:
  # Pixhawk uses different coordinate system verification
  # Keep same safety limits but recalibrate for new airframe
  min_altitude: 2.0
  max_altitude: 50.0
  default_altitude: 10.0
  
attitude_controller:
  # AIC parameters (may need re-tuning for Pixhawk mass/inertia)
  inertia_estimate:
    Ixx: 0.040  # Re-measure with new airframe
    Iyy: 0.040
    Izz: 0.025
  
  control_gains:
    K_R: [5.0, 5.0, 3.0]    # May need adjustment
    K_Omega: [0.3, 0.3, 0.2]
    K: [0.1, 0.1, 0.1]
    c: 2.0
  
  adaptation_params:
    gamma: 0.01
    sigma: 0.001
    beta: 0.04
```

---

## Phase 4: Hardware Calibration (1-2 hours)

### 4.1 Critical Pre-Flight Calibrations

**DO THESE IN ORDER (using Mission Planner or QGroundControl):**

1. **Compass Calibration**
   - Rotate aircraft in 3D figure-8 pattern
   - Clears magnetic interference from new mounting

2. **Accelerometer Calibration**
   - Place Pixhawk level on flat surface
   - Saves gravity vector for current orientation
   - **Critical for attitude estimation**

3. **Radio Calibration**
   - Ensure RC transmitter ranges match (1000-2000 PWM)
   - Critical for manual override

4. **ESC Calibration**
   - Procedure: Arm with stick/modes, advance throttle to max, power cycle
   - Synchronizes ESC ranges with Pixhawk outputs

5. **Motor Order Verification**
   - Arm in LOITER or STABILIZE
   - Gently increase throttle slightly
   - Verify frame lifts evenly (no tilt)
   - Land immediately if asymmetric

### 4.2 AIC Tuning

**Initial setup (conservative):**

```bash
# 1. Set very low control gains first
K_R = [2.0, 2.0, 1.5]      # ~40% of nominal
K_Omega = [0.15, 0.15, 0.1]

# 2. Test in STABILIZE mode (manual throttle, auto attitude)
# 3. Gradually increase gains while monitoring:
#    - Response speed (should be ~0.5s settling time)
#    - Oscillation (should be minimal damping)
#    - Propeller loading (shouldn't stall)

# 4. When stable, enable adaptive learning
# 5. Monitor parameter estimation convergence
```

---

## Phase 5: Testing & Validation (3-4 hours)

### 5.1 Indoor/Bench Testing

```bash
# 1. Connect via USB to ground computer
python3 src/autonomous_flight.py --sim  # If simulation mode available

# 2. Test telemetry
mavproxy.py --master=/dev/ttyUSB0 --baudrate=115200

# 3. Verify sensor readings
# - IMU accelerometer (9.81 m/s² on Z-axis when level)
# - Gyro (should read ~0 when still)
# - Barometer (altitude stable)
# - Compass (consistent heading)
# - RC input (reading stick inputs correctly)

# 4. Test motor outputs
# - In Mission Planner: Initial Setup → Optional Hardware → Motor Test
# - Run each motor 5%, verify correct direction and position
#   Motor 1 (Front-Right) should spin CW
#   Motor 2 (Front-Left) should spin CCW  
#   Motor 3 (Rear-Left) should spin CW
#   Motor 4 (Rear-Right) should spin CCW
```

### 5.2 First Flight Checklist

**PRE-TAKEOFF (15 min before):**

```
□ Battery: Fully charged
□ GPS: Lock with 6+ satellites
□ Compass: Healthy (no red warnings)
□ Radio: Binding verified, sticks responsive
□ Props: Balanced, tight (no play)
□ Failsafes: Enabled and tested
□ Flight plan: Uploaded and verified
□ AIC gains: Conservative initial values
□ Wind: < 10 mph (5 m/s)
□ Clear area: No obstacles, 50m+ radius
□ Camera/Observer: Ready
```

**FLIGHT (manual control):**

```
1. Takeoff manually in STABILIZE mode (50cm-1m)
2. Hover for 30 seconds - verify level and stable
3. Gentle pitch/roll inputs - verify response ~0.5s
4. Descend slowly and land
5. Check battery voltage, motor temps, and logs
```

**IF UNSTABLE:**
- Land immediately (sticks down to 0 throttle)
- Reduce control gains by 50%
- Retest hover
- Repeat until stable

**Second Flight (if stable):**
```
1. Arm → Takeoff to 5m → LOITER for 20 seconds
2. Monitor altitude hold and compass heading
3. Land and review logs
```

**Third Flight (if very stable):**
```
1. Simple square mission (4 waypoints, 10m altitude)
2. Review flight logs for attitude tracking errors
3. Adjust AIC gains if needed (log will show controller performance)
```

### 5.3 Log Analysis

After each flight, review logs:

```bash
# In Mission Planner: Logs → Download Logs

# Check these parameters:
- ATT.Roll, ATT.Pitch, ATT.Yaw (commanded vs actual)
- RATE.RDes, RATE.PDes, RATE.YDes (rate command tracking)
- CTUN.ThI (throttle integrator - should be ~0 for hover)
- BAT.Volt (voltage throughout flight)

# Red flags:
- Attitude lag > 0.2 seconds
- Oscillations in rate control
- Battery voltage sag > 3V
- Motor saturation warnings
```

---

## Phase 6: Optional Upgrades (Future)

### 6.1 Switch to PX4 Firmware (Advanced)

If you want native PX4 AIC module support:

```bash
# Same physical steps, different firmware
git clone https://github.com/PX4/PX4-Autopilot
cd PX4-Autopilot
make px4_fmu-v3  # For Pixhawk 2.4.8

# Update connection in code (MAVLink still works)
# Re-tune all parameters (different defaults)
```

**Pros:** Cleaner architecture, modular design  
**Cons:** Steeper learning curve, requires parameter re-mapping

### 6.2 Add Advanced Sensors

Once basic flight verified:
- Optical flow (altitude/position hold improvements)
- Airspeed sensor (fixed-wing compatibility)
- Lidar (precision landing, obstacle avoidance)

---

## Troubleshooting Quick Reference

| Symptom | Cause | Fix |
|---------|-------|-----|
| **Won't arm** | GPS lock missing | Wait for green LED, 6+ satellites |
| **Rolls to one side** | Motor direction wrong | Swap motor signal to flip rotation direction |
| **Oscillates at hover** | Control gains too high | Reduce K_R, K_Omega by 50% |
| **Drifts sideways** | Compass offset | Re-run compass calibration |
| **Barometer gives wrong altitude** | Not calibrated for terrain | Land, let sensor stabilize 30 seconds |
| **Connection drops** | Serial baud mismatch | Check default_string baud_rate: 115200 for USB |
| **Motors won't spin** | Throttle failsafe | Arm with RC transmitter, not software |
| **AIC learns incorrectly** | Inertia estimate too far off | See IMPLEMENTATION_GUIDE_AIC.md, re-measure J |

---

## Timeline & Effort Summary

| Phase | Time | Difficulty |
|-------|------|-----------|
| 1. Hardware install | 1-2 hrs | Low |
| 2. Firmware setup | 2-3 hrs | Medium |
| 3. Code migration | 2-3 hrs | Low (mostly config) |
| 4. Calibration | 1-2 hrs | Medium |
| 5. Testing | 3-4 hrs | High (flight-critical) |
| **Total** | **9-14 hrs** | **Medium** |

---

## Key Differences: Erlebrain 2 vs Pixhawk 2.4.8

| Aspect | Erlebrain 2 | Pixhawk 2.4.8 |
|--------|-----------|----------------|
| **Firmware** | ArduPilot (custom build) | ArduCopter 4.4.x (standard) |
| **Baud Rate** | 921600 | 115200 (USB) / 57600 (radio) |
| **Power Distribution** | Integrated | Separate PMB (more flexible) |
| **Motor Outputs** | 8 PWM | 6 main + 8 auxiliary |
| **Sensors** | Integrated IMU | Standard Invensense MPU6050 + others |
| **Compass** | Onboard HMC5883L | Usually external u-blox GPS/Compass |
| **Size** | Large (SBC-like) | Standard (80x80mm) |
| **Python Interface** | DroneKit via MAVLink | DroneKit via MAVLink (same) |

---

## Next Steps

1. **TODAY:** Gather hardware (1-2 hrs)
2. **TOMORROW:** Physical installation & mounting (1-2 hrs)
3. **DAY 3:** Firmware installation & calibration (3-4 hrs)
4. **DAY 4:** Code updates & testing (2-3 hrs)
5. **DAY 5:** First flight (2-3 hrs including logs review)
6. **DAYS 6-7:** Tuning & validation (ongoing)

**Start with Phase 1-2, then come back with specific questions once hardware is ready!**
