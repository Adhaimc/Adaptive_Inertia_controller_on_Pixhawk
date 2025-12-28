# Pixhawk 2.4.8 Migration Checklist

## Phase 1: Hardware Preparation
- [ ] Obtain Pixhawk 2.4.8 flight controller
- [ ] Obtain PMB (Power Management Board)
- [ ] Obtain Micro SD card (16GB, class 10+)
- [ ] Obtain USB micro-B cable
- [ ] Verify GPS/Compass module compatibility (u-blox recommended)
- [ ] Gather servo extension cables and jumpers
- [ ] Obtain vibration dampeners/isolators
- [ ] Prepare quadcopter frame for installation

### Physical Installation
- [ ] Remove Erlebrain 2 from frame
- [ ] Mount Pixhawk 2.4.8 with vibration dampers (arrow forward)
- [ ] Connect motors to MAIN OUT 1-4 (verify X configuration)
- [ ] Connect ESCs power to PMB and battery
- [ ] Connect RC receiver to RC IN connector
- [ ] Connect GPS/Compass to GPS connector
- [ ] Connect telemetry module to TELEM1
- [ ] Install Micro SD card
- [ ] Secure all cables with zipties
- [ ] Perform visual inspection of all connections

---

## Phase 2: Firmware & Software Setup

### Install Ground Station Software
- [ ] Install Mission Planner (Windows) OR QGroundControl (Mac/Linux)
- [ ] Install MAVProxy: `pip install MAVProxy`
- [ ] Verify DroneKit installed: `pip install dronekit pymavlink pyyaml`

### Firmware Installation
- [ ] Connect Pixhawk to computer via USB
- [ ] Open Mission Planner / QGroundControl
- [ ] Navigate to Firmware installer
- [ ] Select "Copter" and latest 4.4.x version
- [ ] Click Install Firmware and wait for completion
- [ ] Disconnect and reconnect Pixhawk
- [ ] Verify Pixhawk green light (solid = ready)

### Connection String Setup
- [ ] Identify Pixhawk serial port:
  - macOS USB: `/dev/cu.usbmodem*`
  - Linux USB: `/dev/ttyUSB0`
  - Telemetry radio: `/dev/ttyUSB0` (baud: 57600)
  - WiFi: `udp:192.168.1.X:14550`
- [ ] Update `config/flight_params.yaml` with correct values
- [ ] Test connection: `mavproxy.py --master=/dev/ttyUSB0 --baudrate=115200`

---

## Phase 3: Code Migration

### Python Code Updates
- [ ] Review `src/utils/connection.py` (should need minimal changes)
- [ ] Update `config/flight_params.yaml`:
  - [ ] Change baud_rate: 921600 → 115200
  - [ ] Update connection string for Pixhawk
  - [ ] Add Pixhawk-specific parameters (below)
  - [ ] Update AIC tuning parameters (conservative values)

### AIC Module Integration
- [ ] Verify `src/modules/attitude_controller_aic/` compiles (if using ArduCopter custom build)
- [ ] OR use pre-built ArduCopter 4.4.x (attitude control works automatically)
- [ ] Review `iwg_adapter.hpp` for Erlebrain-specific code (should be none)
- [ ] No changes needed to core control laws (architecture-agnostic)

### Test Code Connectivity
```bash
cd /Users/adhaimc/Documents/GitHub/Erle_brain2
python3 -c "from src.utils.connection import VehicleConnection; print('DroneKit import OK')"
```
- [ ] Verify imports work without errors
- [ ] Run: `python3 src/autonomous_flight.py --help` (verify script structure)

---

## Phase 4: Hardware Calibration

### Pre-Flight Calibration (in Mission Planner / QGroundControl)

**Compass Calibration:**
- [ ] Mission Planner → Initial Setup → Compass
- [ ] Select "Onboard Mag 1" (primary compass)
- [ ] Click "Calibrate Compass"
- [ ] Rotate aircraft in 3D figure-8 pattern (slow, smooth)
- [ ] Wait for "Calibration successful" message

**Accelerometer Calibration:**
- [ ] Mission Planner → Initial Setup → Accelerometer Calibration
- [ ] Place Pixhawk level on flat surface
- [ ] Click "Calibrate Accel" and follow prompts
- [ ] Should complete in 5-10 seconds

**Radio Calibration:**
- [ ] Mission Planner → Initial Setup → Radio Calibration
- [ ] Move sticks to extremes
- [ ] Verify min/max values: 1000-2000 PWM range
- [ ] Center sticks and verify 1500 PWM

**ESC Calibration:**
- [ ] Power off battery
- [ ] Connect Pixhawk to battery (do NOT arm)
- [ ] In Mission Planner → Initial Setup → Optional Hardware → ESC Calibration
- [ ] Follow on-screen prompts (usually: power off/on, advance throttle, etc.)
- [ ] Each ESC should beep twice when calibration complete

**Motor Order Verification:**
- [ ] Arm Pixhawk in STABILIZE mode (via RC: mode switch + arm combination)
- [ ] Increase throttle slightly (5-10%)
- [ ] Verify frame remains level:
  - Motor 1 (Front-Right): Should be spun up
  - Motor 2 (Front-Left): Should be spun up
  - Motor 3 (Rear-Left): Should be spun up
  - Motor 4 (Rear-Right): Should be spun up
- [ ] All four should spin roughly equal
- [ ] Land immediately if asymmetric or oscillations observed

---

## Phase 5: Testing & Validation

### Bench Testing (Indoors, No Props)

**Telemetry Verification:**
- [ ] Connect Pixhawk to computer
- [ ] Open Mission Planner → Data (HUD view)
- [ ] Verify readings appear (attitude, altitude, GPS)
- [ ] Roll Pixhawk by hand → verify Roll value changes
- [ ] Pitch Pixhawk → verify Pitch value changes
- [ ] Check GPS: shows 0 satellites indoors (expected)

**Sensor Health Check:**
- [ ] Mission Planner → Messages → Filter for "AHRS"
- [ ] Should see IMU, compass, barometer health reports
- [ ] All should say "OK" or "healthy"

**Motor Test (Props OFF):**
```
Mission Planner → Initial Setup → Motor Test
- Test Motor 1, 2, 3, 4 at 5% throttle
- Verify direction (CW vs CCW as specified above)
- All spinning smooth, no weird sounds
```
- [ ] Motor 1: CW
- [ ] Motor 2: CCW
- [ ] Motor 3: CW
- [ ] Motor 4: CCW

### First Flight (Outdoor, With Props)

**PRE-TAKEOFF CHECKLIST (15 minutes before):**
- [ ] Battery: Fully charged (voltage at 12.6V for 3S LiPo)
- [ ] GPS: 6+ satellites, green light
- [ ] Compass: Green light, no red warnings
- [ ] Radio: Transmitter on, sticks centered, mode set to STABILIZE
- [ ] Props: Balanced and tight (spin by hand, no play)
- [ ] Failsafes: Set to RTL (Return To Launch)
  - [ ] Radio failsafe: 3 seconds, triggers RTL
  - [ ] Battery failsafe: Enabled, triggers RTL at 11.1V
- [ ] Flight plan: Not needed for first flight
- [ ] Wind: < 10 mph (5 m/s)
- [ ] Clear area: No people/animals, 50m radius
- [ ] Observers: Ready with camera/phone

**FLIGHT PROFILE (Manual Throttle, Auto Attitude):**

**T=0:00 - Arm & Takeoff:**
- [ ] Arm via RC (mode switch + hold)
- [ ] Slowly increase throttle to ~50%
- [ ] Aircraft should climb straight up
- [ ] Target: 50-100cm altitude

**T=0:30 - Hover Test:**
- [ ] Maintain hover for 20-30 seconds
- [ ] Aircraft should hold altitude with minimal throttle input
- [ ] Monitor for oscillations (should be nearly none)

**T=1:00 - Control Response Test:**
- [ ] Gentle pitch forward → verify response ~0.5 seconds
- [ ] Gentle roll right → verify response ~0.5 seconds
- [ ] Return to hover

**T=1:30 - Descent & Landing:**
- [ ] Slowly reduce throttle to near 0
- [ ] Aircraft should descend at ~1 m/s
- [ ] Land on flat surface

**IMMEDIATE POST-FLIGHT:**
- [ ] Remove props
- [ ] Check motor temperature (should be warm, not hot)
- [ ] Check battery voltage (should be ~11.7V min for 3S LiPo)
- [ ] Download flight logs
- [ ] Review logs (see Log Analysis below)

**IF UNSTABLE DURING FLIGHT:**
- Immediately reduce throttle to land
- Reduce control gains by 50% (in config)
- Retest

**IF STABLE:**
- [ ] Second flight: Simple LOITER (hold altitude, hold heading)
  - Arm → Takeoff → Switch to LOITER → Hover 20 seconds → Land
  - Monitor barometer altitude hold accuracy
- [ ] Third flight: Simple square mission (4 waypoints at 10m altitude)
  - Upload mission in Mission Planner
  - Arm → Switch to AUTO → Observe mission execution
  - Land via RC override if needed

### Log Analysis

After each flight:
```bash
# Download logs from Pixhawk
Mission Planner → Logs → Download Logs
```

Open `.bin` log file in Mission Planner:
- [ ] Review "Attitude" tab: Roll/Pitch commanded vs actual
  - Target: < 0.1 rad (5.7°) error during flight
- [ ] Review "Rate" tab: Angular velocity response
  - Target: < 0.2 second response time
- [ ] Review "Throttle" tab: Altitude hold during hover
  - Target: ±0.5m variation
- [ ] Review "Battery" tab: Voltage sag during flight
  - Target: No more than 3V drop from fully charged

**Red Flags in Logs:**
- [ ] Attitude oscillations > 0.3 rad
- [ ] Control saturation warnings
- [ ] Compass glitches (sudden heading jumps)
- [ ] Barometer pressure spikes

---

## Phase 6: AIC Tuning (Post-Flight)

Only do this AFTER stable hover achieved:

**Step 1: Measure Aircraft Inertia**
- [ ] Weigh aircraft
- [ ] Measure from center to each motor (arm length)
- [ ] Calculate: $I = m \times r^2$ (rough estimate)
- [ ] Update `config/flight_params.yaml` → `attitude_controller.inertia_estimate`

**Step 2: Initial Gain Tuning**
- [ ] Set conservative values (50% of nominal):
  - [ ] K_R: [2.5, 2.5, 1.5]
  - [ ] K_Omega: [0.15, 0.15, 0.1]
  - [ ] K: [0.05, 0.05, 0.05]
- [ ] Update `config/flight_params.yaml`

**Step 3: Test in STABILIZE**
- [ ] Fly manual throttle, auto attitude
- [ ] Observe response to stick inputs
- [ ] Should be smooth, no oscillation

**Step 4: Gradually Increase Gains**
- [ ] Increase K_R by 20% each flight
- [ ] Test until oscillations appear
- [ ] Back off to 80% of max value

**Step 5: Enable Adaptive Learning**
- [ ] Set `gamma: 0.01` to enable adaptation
- [ ] Fly several missions
- [ ] Monitor parameter estimates (if using logging)

---

## Success Criteria

**Hover Test (Pass = all green):**
- [ ] Holds altitude within ±0.5m for 30 seconds
- [ ] Maintains heading within ±5° with no correction
- [ ] Throttle input stable (< 10% variation)
- [ ] No oscillations visible

**Flight Test (Pass = all green):**
- [ ] Takeoff smooth and controlled
- [ ] Responds to stick inputs with ~0.5 second delay
- [ ] Loiter holds position within ±1m
- [ ] Landing is smooth and controlled
- [ ] No strange noises or vibrations

**Log Analysis (Pass = all green):**
- [ ] Attitude error < 5° during entire flight
- [ ] No saturation warnings in logs
- [ ] Battery voltage stays > 11V (for 3S LiPo)
- [ ] No GPS/Compass glitches in log

---

## Troubleshooting: Quick Fix Guide

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| **Won't arm** | GPS lock missing, or failsafe triggered | Check Mission Planner Status, wait for 6+ satellites |
| **Rolls/Pitches to side** | Motor direction wrong OR imbalanced props | Check motor spin directions via Motor Test, balance props |
| **Oscillates at hover** | Control gains too high | Reduce K_R and K_Omega by 50%, retest |
| **Drifts in heading** | Compass not calibrated or magnetic interference | Re-run compass calibration, move metal away |
| **Altitude drifts** | Barometer needs calibration | Land on flat surface, wait 30 seconds, retry |
| **Connection drops** | Baud rate mismatch | Verify baud: 115200 for USB, 57600 for radio |
| **Motors won't spin** | Throttle failsafe or not armed | Use RC to arm (mode + stick input), not software |
| **AIC gains have no effect** | Using pre-built firmware without AIC | Check if compiled with custom AIC module |

---

## Signal for "All Good, Move On"

✅ **Next Phase When:**
- Pixhawk boots with green light
- Can hover stably for 30+ seconds
- Logs show < 5° attitude error
- Battery stays above 11V during flight
