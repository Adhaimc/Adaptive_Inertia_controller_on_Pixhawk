# Pixhawk 2.4.8 Migration Resources - Complete Index

## 📚 Migration Documentation Overview

I've created **5 comprehensive guides** to help you migrate from Erle-Brain 2 to Pixhawk 2.4.8. Pick the right guide based on where you are:

---

## 🚀 START HERE (Choose Your Path)

### Path 1: "Just Get It Flying Fast" ⏱️
**→ Read:** [PIXHAWK_QUICK_START.md](./PIXHAWK_QUICK_START.md)

**For:** You want first flight ASAP with minimal setup time  
**Covers:** Hardware swap, firmware install, calibration, first flight  
**Time:** 1-2 hours to first flight  
**Outcome:** Stable hover in STABILIZE mode  

**What you'll do:**
1. Mount Pixhawk on your frame (Day 1)
2. Install ArduCopter firmware (Day 2)
3. Calibrate compass/IMU/radio (Day 3)
4. Fly in STABILIZE mode (Day 4)

---

### Path 2: "I Need Step-by-Step Confirmation" ✅
**→ Read:** [PIXHAWK_MIGRATION_CHECKLIST.md](./PIXHAWK_MIGRATION_CHECKLIST.md)

**For:** You want detailed checkboxes to verify each step  
**Covers:** Hardware, firmware, code, calibration, testing - all with checklists  
**Time:** 2-3 hours per phase  
**Outcome:** Verified stable first flight  

**What you'll do:**
1. Work through Phase 1-6 with explicit checkboxes
2. Mark items off as completed
3. Know exactly when you're ready to move forward

---

### Path 3: "I Want to Understand Everything" 📖
**→ Read:** [PIXHAWK_2_4_8_MIGRATION_GUIDE.md](./PIXHAWK_2_4_8_MIGRATION_GUIDE.md)

**For:** You want comprehensive technical background  
**Covers:** Hardware details, firmware options, architecture differences, tuning theory  
**Time:** 3-4 hours to understand, then 9-14 hours to execute  
**Outcome:** Expert-level understanding + flight-ready system  

**What you'll do:**
1. Understand all hardware differences (connectors, pins, power)
2. Learn firmware options (ArduCopter vs PX4)
3. Understand code migration (what changes, what doesn't)
4. Deep dive into AIC tuning theory
5. Execute migration with confidence

---

### Path 4: "I Want Custom AIC Integration" 🔧
**→ Read:** [PIXHAWK_AIC_COMPILATION_GUIDE.md](./PIXHAWK_AIC_COMPILATION_GUIDE.md)

**For:** You want native AIC module compiled into firmware  
**Covers:** ArduPilot compilation, module integration, build system  
**Time:** 2-3 hours setup, then 1-2 hours compilation  
**Outcome:** Custom firmware with AIC module  

**What you'll do:**
1. Set up build environment (Linux/macOS)
2. Clone ArduPilot repository
3. Copy your AIC module
4. Configure CMakeLists.txt
5. Compile firmware for Pixhawk 2.4.8
6. Upload via USB

**⚠️ Note:** Only do this AFTER you've flown successfully with pre-built firmware!

---

## 📋 New Configuration Files

### [config/flight_params_pixhawk.yaml](./config/flight_params_pixhawk.yaml)

**Template configuration for Pixhawk 2.4.8**

Contains:
- ✅ Connection strings (USB, telemetry radio, WiFi options)
- ✅ Hardware settings (motor layout, compass declination)
- ✅ Flight parameters (altitude, speed, safety limits)
- ✅ AIC controller parameters (inertia, control gains)
- ✅ Calibration settings
- ✅ Extensive comments for each parameter

**How to use:**
```bash
# Copy to active config:
cp config/flight_params_pixhawk.yaml config/flight_params.yaml

# Edit your specific values:
nano config/flight_params.yaml

# Key things to customize:
# - connection.default_string (your Pixhawk USB port)
# - pixhawk.compass_declination (your location)
# - attitude_controller.inertia_estimate (your aircraft)
# - attitude_controller.control_gains (start conservative)
```

---

## 🔗 Quick Navigation

| Document | Purpose | Read Time | Difficulty |
|----------|---------|-----------|-----------|
| [PIXHAWK_QUICK_START.md](./PIXHAWK_QUICK_START.md) | Fast path to first flight | 15 min | Low |
| [PIXHAWK_MIGRATION_CHECKLIST.md](./PIXHAWK_MIGRATION_CHECKLIST.md) | Detailed verification steps | 30 min | Low |
| [PIXHAWK_2_4_8_MIGRATION_GUIDE.md](./PIXHAWK_2_4_8_MIGRATION_GUIDE.md) | Complete technical guide | 60 min | Medium |
| [PIXHAWK_AIC_COMPILATION_GUIDE.md](./PIXHAWK_AIC_COMPILATION_GUIDE.md) | Firmware compilation | 45 min | High |
| [config/flight_params_pixhawk.yaml](./config/flight_params_pixhawk.yaml) | Configuration template | 20 min | Low |

---

## 🎯 Decision Tree: Which Guide Should I Use?

```
┌─ Are you replacing Erlebrain hardware right now?
│
├─ YES ──┬─ Do you want to understand the full process?
│        │
│        ├─ YES → Read PIXHAWK_2_4_8_MIGRATION_GUIDE.md
│        │
│        └─ NO ──┬─ Do you like step-by-step checklists?
│                │
│                ├─ YES → PIXHAWK_MIGRATION_CHECKLIST.md
│                │
│                └─ NO → PIXHAWK_QUICK_START.md
│
└─ LATER (after first flight works) ──→ Want custom AIC?
                                         → PIXHAWK_AIC_COMPILATION_GUIDE.md
```

---

## ⚡ TL;DR for Impatient People

**The absolute minimum you need:**

1. **Read:** [PIXHAWK_QUICK_START.md](./PIXHAWK_QUICK_START.md) (15 minutes)
2. **Gather:** Hardware listed in Phase 1 of guide
3. **Physically:** Mount Pixhawk, connect motors/battery/GPS/radio
4. **Download:** [QGroundControl](https://qgroundcontrol.com/) or Mission Planner
5. **Flash:** ArduCopter 4.4.2 firmware (automatic via ground station)
6. **Configure:** Copy `config/flight_params_pixhawk.yaml` and update connection string
7. **Calibrate:** Compass → Accel → Radio → Motors (20 minutes)
8. **Fly:** Hover in STABILIZE mode (2 hours)

**Expected outcome:** Stable quadcopter in 2-3 days

---

## 🚨 Critical Warnings

### ⚠️ Baud Rate Change
```
Erlebrain 2:  921600
Pixhawk 2.4.8: 115200 (USB) / 57600 (radio)

If you don't change this, connection WILL FAIL.
Update in: config/flight_params.yaml
connection:
  baud_rate: 115200  ← NOT 921600!
```

### ⚠️ Motor Pinout
```
Pixhawk MAIN OUT 1-4:
1 = Front-Right (Roll control)
2 = Front-Left (Pitch control)
3 = Rear-Left (Throttle)
4 = Rear-Right (Yaw control)

Wrong wiring → Aircraft tumbles on takeoff
```

### ⚠️ Compass Calibration
```
If compass not calibrated:
- Aircraft drifts in heading
- Missions go to wrong waypoints
- Can damage GPS lock during flight

Spend 5 minutes on compass calibration = hours saved troubleshooting
```

---

## 📊 Migration Timeline

| Phase | Task | Time | Tools |
|-------|------|------|-------|
| **Day 1** | Physical hardware swap | 2 hrs | Screwdriver, soldering iron |
| **Day 2** | Firmware installation | 1 hr | QGroundControl, USB cable |
| **Day 3** | Calibration | 1 hr | Mission Planner |
| **Day 4** | First flight test | 2 hrs | Outdoor space, RC transmitter |
| **Day 5+** | Tuning & validation | 2-4 hrs | Flight logs, config editor |
| **TOTAL** | End-to-end migration | **8-11 hrs** | — |

---

## 🆘 Troubleshooting Guide

### "I can't find my connection string"

**macOS:**
```bash
ls /dev/cu.usb*
# Look for: /dev/cu.usbmodem14101 or similar
```

**Linux:**
```bash
ls /dev/ttyUSB*
# Look for: /dev/ttyUSB0
```

### "DroneKit connection times out"

1. Check baud rate (must be 115200)
2. Verify port name (run commands above)
3. Test with: `mavproxy.py --master=/dev/ttyUSB0 --baudrate=115200`

### "Aircraft oscillates on hover"

1. Reduce K_R by 50% in config
2. Retest
3. See "AIC Tuning" section in migration guide

### "Won't arm - red warning in Mission Planner"

1. Check GPS (need 6+ satellites)
2. Check compass (red = re-calibrate)
3. Check battery (need > 11V for 3S LiPo)
4. See full troubleshooting in checklist document

---

## 📚 Additional Resources

### ArduPilot Official
- Copter Setup: https://ardupilot.org/copter/docs/initial-setup.html
- Pixhawk Setup: https://ardupilot.org/copter/docs/pixhawk-setup-v1-2.html
- Building from Source: https://ardupilot.org/dev/docs/building-the-code.html

### Pixhawk Hardware
- Pixhawk 2.4.8 Schematic: Check manufacturer documentation
- Pinout Reference: In PIXHAWK_2_4_8_MIGRATION_GUIDE.md

### Your AIC Module
- AIC Implementation: [IMPLEMENTATION_GUIDE_AIC.md](./IMPLEMENTATION_GUIDE_AIC.md)
- AIC Theory: Reference the paper cited in implementation guide

---

## ✅ Success Checklist

After completing migration, verify:

- [ ] Pixhawk powers on (green light within 2 seconds)
- [ ] Can connect via DroneKit: `python src/autonomous_flight.py --help` works
- [ ] GPS locks with 6+ satellites in <30 seconds
- [ ] Compass calibrated (no red warnings in Mission Planner)
- [ ] Motors spin in correct directions (verified via Motor Test)
- [ ] Hovers level for 30+ seconds at altitude
- [ ] Responds to stick inputs with <0.5s delay
- [ ] Flight logs show <5° attitude error
- [ ] Battery voltage stays >11V during flight
- [ ] Can land smoothly on RC override

**All green?** → You've successfully migrated! 🎉

---

## 🎓 Learning Path

If this is your first time with Pixhawk:

1. **First:** PIXHAWK_QUICK_START.md (what to do)
2. **Then:** PIXHAWK_2_4_8_MIGRATION_GUIDE.md (why you do it)
3. **Later:** PIXHAWK_AIC_COMPILATION_GUIDE.md (advanced customization)
4. **Finally:** IMPLEMENTATION_GUIDE_AIC.md (control law deep dive)

---

## 📞 Getting Help

If you get stuck:

1. **Check the relevant guide** (use decision tree above)
2. **Review the PIXHAWK_MIGRATION_CHECKLIST.md** (find your phase)
3. **Search "Troubleshooting" in that guide**
4. **Check error output in Mission Planner logs**
5. **Review flight logs after first flight**

**Most issues are:**
- ❌ Wrong baud rate → Fix in config (115200!)
- ❌ Motor pinout wrong → Re-wire or reverse direction
- ❌ Compass not calibrated → Spend 5 minutes on calibration
- ❌ Control gains too high → Reduce by 50%, retest
- ❌ Battery too weak → Fully charge or replace

---

## 📝 Configuration Checklist

Before first flight, verify these in `config/flight_params.yaml`:

```yaml
✓ connection.default_string → Your USB port
✓ connection.baud_rate → 115200 (NOT 921600!)
✓ pixhawk.compass_declination → Your location
✓ flight.min_altitude → 2.0 (or higher for your location)
✓ flight.max_altitude → 50.0 (safe for first flight)
✓ attitude_controller.inertia_estimate → Your aircraft measurements
✓ attitude_controller.control_gains → Conservative initial values
```

---

## 🏁 Next Steps

**Pick your path from the decision tree above and start with the recommended guide!**

Questions? Check the relevant guide or the full migration directory:

```
Erle_brain2/
├── PIXHAWK_QUICK_START.md                  ← Start here
├── PIXHAWK_MIGRATION_CHECKLIST.md
├── PIXHAWK_2_4_8_MIGRATION_GUIDE.md
├── PIXHAWK_AIC_COMPILATION_GUIDE.md
├── config/
│   └── flight_params_pixhawk.yaml          ← Copy and edit this
├── IMPLEMENTATION_GUIDE_AIC.md             ← For tuning details
└── (rest of your project)
```

---

**Good luck with the migration! You've got this.** ✈️

> *Last updated: December 27, 2025*  
> *For Pixhawk 2.4.8 + ArduCopter 4.4.x*
