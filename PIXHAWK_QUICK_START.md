# Pixhawk 2.4.8 Quick Start Guide

## TL;DR - Start Here

You're switching from **Erle-Brain 2 → Pixhawk 2.4.8**. Here's the fastest path to first flight:

### Day 1: Physical Swap (2 hours)
1. Remove Erlebrain, mount Pixhawk with vibration dampers
2. Connect motors to MAIN OUT 1-4 (verify X-config pin order)
3. Connect battery via Power Management Board (PMB)
4. Connect GPS, RC receiver, telemetry radio
5. Insert Micro SD card

### Day 2: Firmware (1 hour)
1. Download **Mission Planner** (Windows) or **QGroundControl** (Mac)
2. Plug Pixhawk into computer via USB
3. Install **ArduCopter 4.4.2** firmware (auto-download via ground station)
4. Restart Pixhawk (watch for solid green light)

### Day 3: Calibration (1 hour)
1. **Compass calibration**: Mission Planner → Initial Setup → Compass, rotate aircraft 3D
2. **Accelerometer calibration**: Place level, click Calibrate Accel
3. **Radio calibration**: Verify RC sticks center at 1500 PWM
4. **ESC calibration**: Follow on-screen procedure
5. **Motor test**: Verify motors spin in correct direction, no reverse

### Day 4: First Flight (2 hours)
1. Update `config/flight_params_pixhawk.yaml` with your connection string:
   - Find port: `ls /dev/cu.usb*` (macOS) or `/dev/ttyUSB0` (Linux)
   - Baud: **Always 115200 for USB**
2. Copy template to active config:
   ```bash
   cp config/flight_params_pixhawk.yaml config/flight_params.yaml
   ```
3. Outdoors, props on, test hover in STABILIZE mode
4. Monitor logs for attitude errors < 5°
5. If stable, try simple mission (4 waypoints)

---

## Critical Differences: Erlebrain vs Pixhawk

| Feature | Erlebrain 2 | Pixhawk 2.4.8 |
|---------|-----------|---------------|
| **Baud Rate** | 921600 | **115200** (USB) |
| **Firmware** | Custom ArduCopter | Standard ArduCopter 4.4.x |
| **Motor Pins** | Custom | MAIN OUT 1-4 |
| **Power** | Integrated | External PMB |
| **Size** | Large | Compact (80x80mm) |

⚠️ **Change connection baud from 921600 to 115200 immediately or connection will fail!**

---

## Connection String Cheat Sheet

### Find Your Pixhawk Port

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

**Update config/flight_params.yaml:**
```yaml
connection:
  default_string: '/dev/cu.usbmodem14101'  # YOUR PORT HERE
  baud_rate: 115200  # NOT 921600!
```

---

## Motor Wiring (X Configuration)

**Pixhawk MAIN OUT pin order:**

```
    FL (Front-Left)     FR (Front-Right)
           2                  1
           
           
           4                  3
    RL (Rear-Left)      RR (Rear-Right)
```

**Wire your ESCs to:**
- Motor 1: Front-Right → Pixhawk MAIN OUT 1
- Motor 2: Front-Left → Pixhawk MAIN OUT 2
- Motor 3: Rear-Left → Pixhawk MAIN OUT 3
- Motor 4: Rear-Right → Pixhawk MAIN OUT 4

Spin directions (viewed from above):
- Motors 1, 3: **Clockwise (CW)**
- Motors 2, 4: **Counter-Clockwise (CCW)**

✅ Verify in Mission Planner: Initial Setup → Motor Test

---

## Calibration Checklist

Before first flight, do these in order:

### 1. Compass Calibration
```
Mission Planner → Initial Setup → Compass
→ Select "Onboard Mag 1"
→ Click "Calibrate Compass"
→ Rotate aircraft slowly in 3D figure-8 for 60 seconds
→ Green "Success" message = done
```

### 2. Accelerometer Calibration
```
Mission Planner → Initial Setup → Accelerometer Calibration
→ Place Pixhawk flat and level on table
→ Click "Calibrate Accel"
→ Wait 5 seconds (don't move)
→ Green "Success" = done
```

### 3. Radio Calibration
```
Mission Planner → Initial Setup → Radio Calibration
→ Move throttle stick to full range (bottom, top)
→ Move roll stick to full range (left, right)
→ Move pitch stick to full range (forward, back)
→ Move yaw stick to full range (left, right)
→ Verify all channels show 1000 min, 2000 max
→ Center all sticks, verify 1500 PWM
```

### 4. Motor Order Test
```
Mission Planner → Initial Setup → Motor Test
→ Power on (do NOT attach props!)
→ Arm via RC transmitter (mode switch + stick input)
→ Test Motor 1 at 5% (should spin)
→ Verify rotation direction and position match diagram above
→ Repeat for Motors 2, 3, 4
→ Disarm
```

---

## First Flight: Step-by-Step

### Pre-Flight (15 min before)
- [ ] Battery fully charged
- [ ] GPS lock with 6+ satellites (green light in HUD)
- [ ] RC transmitter ON, sticks centered, mode = STABILIZE
- [ ] Props installed and balanced
- [ ] No people/animals within 50 meters
- [ ] Clear sky view (no trees/buildings blocking GPS)

### Takeoff
1. Arm via RC (mode switch + hold sticks input, or use arm command)
2. Watch for blue light (armed)
3. Slowly increase throttle to 50%
4. Aircraft should climb straight up
5. **Stop if it tilts unexpectedly** → Land, reduce gains

### Hover Test (30 seconds)
1. Reduce throttle to hover (~40% for typical quad)
2. Aircraft should hold altitude with minimal adjustment
3. **Watch for oscillations** (regular rocking = gains too high)
4. Verify GPS heading stable (should not drift)
5. Observe battery voltage (should be > 11V for 3S LiPo)

### Control Test (20 seconds)
1. Gentle pitch forward → should nose down smoothly
2. Gentle roll right → should lean right smoothly  
3. Gentle yaw right → should rotate smoothly
4. All responses should feel smooth, no jerky movements

### Landing
1. Reduce throttle slowly to 0%
2. Let aircraft descend at ~1 m/s
3. Land on flat ground
4. Reduce throttle to near-zero to disarm

### Immediate Post-Flight
1. Check battery voltage (should be >11V)
2. Feel motors for heat (warm ok, hot = problem)
3. Download flight logs (see below)

---

## Download & Analyze Flight Logs

### Download Logs
```
Mission Planner → Logs → Download Logs → Select latest .bin file
```

### Review Key Parameters
Open `.bin` in Mission Planner, check "Attitude" tab:
- **Roll/Pitch error**: Should be < 5° (0.09 rad) during hover
- **Response time**: Should be < 0.5 seconds to stick input
- **Oscillation**: Should damp out in 1-2 cycles

### Red Flags 🚩
- Attitude error > 10° → Control gains too high or compass misaligned
- Oscillations that grow → Gain instability, reduce K_R, K_Omega
- Voltage sag > 3V → Battery too weak or ESCs not calibrated
- Heading drift > 10° → Compass not calibrated, retry

---

## Troubleshooting

### Can't Connect via DroneKit
```bash
# Test connection first:
mavproxy.py --master=/dev/ttyUSB0 --baudrate=115200

# If that fails:
# 1. Check port name: ls /dev/cu.usb*
# 2. Check baud rate (must be 115200)
# 3. Try different USB port/cable
```

### Won't Arm
```
Check Mission Planner Status window:
- GPS? Need 6+ satellites
- Compass healthy? Red = re-calibrate
- Battery? Needs > 11V for 3S LiPo
- RC connected? Transmitter must be on
```

### Oscillates During Hover
1. **Reduce K_R by 50%** (control gain too high)
2. Retest hover
3. Gradually increase gains until oscillations return
4. Back off to 80% of that value

### Drifts Sideways
1. **Compass issue** → Re-run compass calibration
2. **Props imbalanced** → Balance or replace props
3. **Motor direction wrong** → Check motor test output directions

### Battery Voltage Drops Too Fast
1. Check ESCs fully calibrated (redo ESC calibration)
2. Verify battery voltage at start (should be ~12.6V for 3S)
3. Reduce control gains (less aggressive = less power draw)

---

## Next Steps After Stable Hover

### When Stable (< 0.5m altitude error, smooth control):

**Option 1: Fly Simple Missions**
```bash
# Create 4-waypoint square mission
# Arm → Switch to AUTO → Watch it fly
# Land via RC override
```

**Option 2: Tune AIC Controller**
```bash
# Edit config/flight_params.yaml:
# - Increase K_R gradually (5→6→7)
# - Test each day
# - Stop when oscillations appear
# - Back off 10-20%
```

**Option 3: Add Sensors/Features**
- Optical flow (altitude hold improvement)
- Airspeed sensor (fixed-wing compatibility)
- Lidar (collision avoidance)

---

## Pixhawk 2.4.8 Pin Reference

### MAIN Connectors (Top of Pixhawk)
```
MAIN OUT:     Motor outputs 1-4 (+ 5V power rail)
AUX OUT:      Auxiliary outputs (usually unused for quadcopter)
POWER:        Battery input (via PMB)
SWITCH:       Safety switch connector
```

### TELEM Connectors (Side of Pixhawk)
```
TELEM1:       Main telemetry (WiFi, 3DR radio, ground station)
TELEM2:       Secondary (spare, often GPS/compass on same connector)
GPS:          GPS/Compass module (6-pin Molex)
```

### Bottom Connectors
```
I2C:          Auxiliary I2C (spare sensors)
CAN:          CAN bus (future expansion)
USART:        Debug serial (advanced users)
```

---

## Software Installation Reminders

### On Development Computer:
```bash
# Required:
pip install dronekit pymavlink pyyaml

# Recommended:
pip install MAVProxy  # For command-line testing
pip install qgroundcontrol  # GUI mission planner
```

### On Pixhawk:
```
Nothing to install - firmware only.
Just flash ArduCopter 4.4.2 via ground station.
```

---

## Success Criteria

✅ **First Flight Success** (all must pass):
- [ ] Pixhawk boots with solid green light
- [ ] Can arm via RC transmitter
- [ ] Hovers for 30+ seconds at altitude
- [ ] Responds smoothly to control stick inputs
- [ ] Battery voltage stays > 11V
- [ ] Landing is smooth and controlled
- [ ] Flight logs show < 5° attitude error

---

## Video Guides

**Pixhawk 2.4.8 Setup:**
- ArduPilot official: https://ardupilot.org/copter/
- Mission Planner tutorial: https://www.youtube.com/@ArduPilot

---

## Need Help?

**Common Issues → Check these files:**
1. **Connection problems** → See "Connection String Cheat Sheet" above
2. **Unstable flight** → See "Troubleshooting" section
3. **Motor issues** → Verify wiring in "Motor Wiring (X Configuration)" diagram
4. **Calibration** → Step-by-step in "Calibration Checklist" above
5. **Advanced tuning** → See `IMPLEMENTATION_GUIDE_AIC.md`

**File Reference:**
- `PIXHAWK_MIGRATION_GUIDE.md` - Detailed migration steps
- `PIXHAWK_MIGRATION_CHECKLIST.md` - Step-by-step checklist
- `config/flight_params_pixhawk.yaml` - Pixhawk-specific parameters
- `IMPLEMENTATION_GUIDE_AIC.md` - AIC controller tuning

---

**Good luck with the migration! Start with Day 1 (physical swap) and work through each phase. Don't skip calibration - it's critical for safe flight.** ✈️
