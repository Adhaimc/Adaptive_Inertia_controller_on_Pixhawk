# Three-Phase Flight Test Checklist

## Pre-Test Preparation (Do This FIRST)

### Hardware Checklist
- [ ] Pixhawk connected via USB cable
- [ ] Battery fully charged (>12.4V for 3S)
- [ ] Propellers removed (for Phase 1-2)
- [ ] All connectors seated properly
- [ ] No loose parts or exposed wires
- [ ] Quad placed on flat, level surface
- [ ] USB port working (test with `ls /dev/cu.usb*`)

### Software Checklist
- [ ] All dependencies installed: `pip install dronekit pymavlink pyyaml`
- [ ] config/flight_params.yaml updated with correct USB port
- [ ] test_all_phases.py script exists and is executable
- [ ] No other serial connections (close Mission Planner, etc.)

### Environment Checklist
- [ ] Clear flat surface (2m x 2m minimum)
- [ ] Tether rope available for Phase 3 (2-3 meter rope)
- [ ] All people briefed on flight test procedures
- [ ] No obstacles or pets nearby

---

## Phase 1: USB Connection Test (5 min)
**Goal:** Verify communication with Pixhawk

### Pre-Phase 1
- [ ] Pixhawk powered on (lights visible)
- [ ] USB cable connected
- [ ] Config file has correct port

### During Phase 1
- Script will:
  - [ ] Connect to Pixhawk via USB
  - [ ] Read vehicle information
  - [ ] Check battery voltage
  - [ ] Start status monitoring
  - [ ] Display all readings

### Success Criteria (All Must Pass)
- [ ] Connection successful (no timeout)
- [ ] Vehicle info displays
- [ ] Battery > 11V
- [ ] Attitude readings stable (R/P/Y show values)
- [ ] Status monitoring starts

### If Phase 1 Fails
- [ ] Check USB port: `ls /dev/cu.usb*`
- [ ] Try different USB cable
- [ ] Try different USB port on Mac
- [ ] Verify config/flight_params.yaml port is correct
- [ ] Restart Pixhawk (power cycle)

---

## Phase 2: Benchtop Test (10 min)
**Goal:** Verify arm/disarm and throttle control (NO PROPS)

### Pre-Phase 2
- [ ] ALL PROPELLERS REMOVED AND STORED SAFELY
- [ ] Quad on flat table
- [ ] Battery still > 11V
- [ ] Clear the area around quad

### During Phase 2
Script will:
- [ ] Set STABILIZE mode
- [ ] Arm vehicle
- [ ] Test neutral stick position
- [ ] Ramp throttle 0% → 50% → 0%
- [ ] Test roll, pitch, yaw commands
- [ ] Disarm vehicle

### What You'll Observe
- [ ] Motors should NOT spin (no props)
- [ ] You may hear motor tones increase/decrease with throttle
- [ ] Attitude commands might cause slight tilt (without props, subtle)
- [ ] All commands respond smoothly

### Success Criteria (All Must Pass)
- [ ] Arm successful
- [ ] Throttle ramps smoothly
- [ ] Attitude commands acknowledge
- [ ] Disarm successful
- [ ] No error messages

### If Phase 2 Fails
- [ ] Check Pixhawk is armable: should show `Armable: True`
- [ ] Verify GPS lock (not critical for STABILIZE mode)
- [ ] Check compass is healthy (may need recalibration)
- [ ] Ensure battery > 11V

---

## Phase 3: Tethered Hover Test (20 min)
**Goal:** First flight - gentle hover on tether

### Pre-Phase 3 (CRITICAL SAFETY)
- [ ] Install all 4 propellers correctly
  - Motors 1, 3: Clockwise (viewed from above)
  - Motors 2, 4: Counter-clockwise
- [ ] Propellers balanced (no wobble)
- [ ] Battery fully charged (>12.4V)
- [ ] Attach 2-3 meter tether rope to quad frame
- [ ] Secure tether at ground (anchor/stake)
- [ ] Clear 5m radius area completely
- [ ] NO PEOPLE within 10 meters
- [ ] NO PETS nearby
- [ ] All people wearing long sleeves (prop safety)
- [ ] Quad on ground, props not touching anything

### During Phase 3
Script will:
- [ ] Arm vehicle
- [ ] Gently ramp throttle 0% → 60% over 5 seconds
  - **WATCH:** Quad should lift off smoothly
  - **WATCH:** Attitude should stay level
  - **WATCH:** No violent oscillations
- [ ] Hover at ~45% throttle for 10 seconds
  - **LISTEN:** Motor sounds smooth and steady
  - **WATCH:** Altitude stable
  - **WATCH:** No drifting or tilting
- [ ] Test small control inputs (2° roll/pitch)
  - **WATCH:** Responsive but not jerky
- [ ] Gently descend over 5 seconds
  - **WATCH:** Smooth landing
- [ ] Disarm

### What You'll Observe (Normal Hover)
- ✅ Liftoff is smooth and steady
- ✅ Hovers 0.5-1m above ground
- ✅ Attitude stays level (< 5° error)
- ✅ Only minor adjustments needed
- ✅ Landing is gentle
- ✅ Motors stop cleanly

### What You'll Observe (Problems)
- ❌ Violent oscillations → Gain too high, land immediately
- ❌ Won't liftoff → Check motor directions, throttle response
- ❌ Drifts constantly → Compass or prop balance issue
- ❌ One side much higher → Motor or ESC issue

### Success Criteria (All Must Pass)
- [ ] Liftoff smooth and controlled
- [ ] Hovers stable (±0.5m)
- [ ] Attitude error < 5°
- [ ] Control inputs responsive
- [ ] Landing smooth and controlled
- [ ] No oscillations or instability

### If Phase 3 Fails - Troubleshooting

**Won't Arm:**
- [ ] GPS lock needed? Check for 6+ satellites
- [ ] Compass error? Too close to metal, recalibrate
- [ ] Battery low? Check voltage > 11V

**Oscillates/Unstable:**
- [ ] Motor direction wrong? Check Phase 2 motor test
- [ ] Propeller imbalanced? Replace props
- [ ] Gain too high? (Will fix in tuning)
- [ ] Props loose? Tighten motor bolts

**Won't Liftoff:**
- [ ] Check motor directions (should match diagram)
- [ ] ESC reversed? Swap two wires on one ESC
- [ ] Throttle not reaching motors? Check arming

**Drifts Sideways:**
- [ ] Compass miscalibrated → Redo compass calibration
- [ ] Props unbalanced → Replace props
- [ ] Motor/ESC issue → Test individual motors

---

## Post-Flight Checklist

### Immediate (Right After Landing)
- [ ] Disarm and power down
- [ ] Check battery voltage (should be > 10.5V)
- [ ] Feel motors (warm is OK, hot means problem)
- [ ] Visually inspect for damage
- [ ] Check all prop bolts are tight

### Download Logs
```bash
# Use Mission Planner to download logs
# Check attitude errors during hover (should be < 2°)
```

### Review Results
- [ ] Voltage sag < 3V during hover
- [ ] Attitude error < 5° steady-state
- [ ] No oscillations in logs
- [ ] Response time < 1 second to commands

---

## Success Summary

If all three phases pass:

🎉 **Congratulations!**
- ✅ Your Pixhawk is working
- ✅ RC override control is functional
- ✅ First stable hover achieved
- ✅ Ready for AIC controller integration

**Next Steps:**
1. Review flight logs for attitude/energy use
2. Integrate AIC controller (see RC_OVERRIDE_INTEGRATION.md)
3. Tune control gains if needed
4. Run simple waypoint missions

---

## Emergency Procedures

### If Quad Goes Out of Control
- **IMMEDIATELY:** Lower throttle to 0
- **THEN:** Kill power (remove battery)
- **AFTER:** Recover quad and inspect

### If Tether Breaks
- **DON'T CHASE:** Let quad fall
- **RECOVER:** Walk around to find it
- **INSPECT:** Check for damage before next test

### If Person Gets Struck by Prop
- **STOP ALL:** Kill power immediately
- **ASSESS:** Check for injury
- **CALL EMERGENCY:** 911 if needed

---

## Contact/Support

**Before Test:**
- Make sure USB port is correct: `ls /dev/cu.usb*`
- Verify battery is charged

**During Test:**
- Read script prompts carefully
- Don't skip safety checks
- Stop immediately if anything looks wrong

**After Test:**
- Review the test summary
- Check battery voltage
- Download and review logs

**Troubleshooting:**
- See RC_OVERRIDE_README.md
- See PIXHAWK_QUICK_START.md
- See IMPLEMENTATION_GUIDE_AIC.md

---

**Ready?** Run: `python test_all_phases.py --port /dev/YOUR_PORT`
