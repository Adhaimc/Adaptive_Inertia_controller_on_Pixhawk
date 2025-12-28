# Complete Autonomous Flight Workflow

## 🎯 Overview

This document provides the complete workflow from setup to autonomous flight execution with Erle-Brain 2.

---

## Phase 1: Initial Setup (One-time)

### 1.1 Hardware Setup
```
□ Mount Erle-Brain 2 on quadcopter frame
□ Connect all ESCs to motor outputs  
□ Connect RC receiver (for safety override)
□ Connect GPS module
□ Connect battery with voltage monitoring
□ Verify all connections are secure
```

### 1.2 Software Installation
```bash
# SSH into Erle-Brain 2
ssh erle@erle-brain-2.local
# Password: holaerle

# Clone repository
cd ~
git clone <your-repo-url> Erle_brain2
cd Erle_brain2

# Run setup script
chmod +x setup.sh
./setup.sh
```

### 1.3 Configuration
```bash
# Edit flight parameters
nano config/flight_params.yaml

Key settings to verify:
- connection.default_string
- flight.max_altitude
- flight.default_speed
- safety.battery_critical
- geofence.radius
```

---

## Phase 2: Pre-Flight (Every Time)

### 2.1 System Check
```bash
# Check ArduPilot is running
ps aux | grep arducopter

# If not running, start it
# (specific command depends on your setup)
```

### 2.2 Connection Test
```bash
# Test vehicle connection
python3 src/utils/connection.py

Expected output:
✓ Connection successful!
  Mode: GUIDED
  Armed: False
  Battery: 12.4V
  GPS: 3D Fix, 10 satellites
```

### 2.3 Telemetry Check
```bash
# Monitor telemetry for 30 seconds
python3 src/telemetry_monitor.py

Verify:
□ GPS has 3D fix (fix_type: 3)
□ 6+ satellites visible
□ Battery voltage > 11.1V
□ All sensors responding
□ No error messages
```

### 2.4 Update Mission Coordinates
```bash
# Edit mission file with ACTUAL GPS location
nano missions/simple_square.json

⚠️ CRITICAL: Use your actual GPS coordinates!
Get current position from telemetry monitor
```

---

## Phase 3: First Flight (Simulation)

### 3.1 SITL Setup (on development computer)
```bash
# Install ArduPilot SITL (one-time)
cd ~
git clone https://github.com/ArduPilot/ardupilot
cd ardupilot
git submodule update --init --recursive

# Start SITL simulator
cd ArduCopter
sim_vehicle.py --console --map
```

### 3.2 Test Flight in Simulation
```bash
# In another terminal
cd ~/Erle_brain2

# Test simple hover
python3 src/autonomous_flight.py \
  --connection tcp:127.0.0.1:5760 \
  --test \
  --altitude 10 \
  --duration 15

Expected sequence:
1. Connection to SITL
2. Pre-flight checks
3. Arming
4. Takeoff to 10m
5. Hover for 15s
6. Landing
7. Disarm

✓ If successful in simulation, proceed to real flight
✗ If failed, check logs and fix issues
```

---

## Phase 4: Real Flight (Progressive Testing)

### 4.1 Test 1: Low Altitude Hover
```bash
# On Erle-Brain 2, outside with clear GPS

# Physical checklist:
□ Clear area (no people/obstacles within 50m)
□ RC transmitter on and ready
□ Battery fully charged
□ Weather conditions good (no wind/rain)
□ Safety observer present

# Run test
python3 src/autonomous_flight.py \
  --test \
  --altitude 2 \
  --duration 10

# Monitor in another SSH session
python3 src/telemetry_monitor.py

What to expect:
1. Pre-flight checks (takes 10-30 seconds)
2. Arming (motors spin up)
3. Takeoff (slow climb to 2m)
4. Hover (stable at 2m for 10s)
5. Landing (slow descent)
6. Automatic disarm

✓ Success: Proceed to Test 2
✗ Failure: Check logs/errors, fix, retry
```

### 4.2 Test 2: Normal Altitude Hover
```bash
# Same precautions as Test 1

python3 src/autonomous_flight.py \
  --test \
  --altitude 10 \
  --duration 20

✓ Success: Proceed to Test 3
✗ Failure: Diagnose and fix
```

### 4.3 Test 3: Simple Square Mission
```bash
# Edit mission with your location
nano missions/simple_square.json

# Verify coordinates are correct (within 20m of home)
python3 -c "
from src.mission_planner import MissionPlanner
import json
with open('missions/simple_square.json') as f:
    mission = json.load(f)
    print('Waypoints:')
    for wp in mission['waypoints']:
        print(f\"  {wp['id']}: {wp['lat']:.6f}, {wp['lon']:.6f}, {wp['alt']}m\")
"

# Execute mission
python3 src/autonomous_flight.py \
  --mission missions/simple_square.json

What happens:
1. Pre-flight checks
2. Takeoff to default altitude
3. Fly to each waypoint in sequence
4. Return to launch (RTL)
5. Automatic landing

✓ Success: Ready for complex missions
```

### 4.4 Test 4: Complex Waypoint Mission
```bash
# Edit waypoint mission
nano missions/waypoint_mission.json

# Execute
python3 src/autonomous_flight.py \
  --mission missions/waypoint_mission.json
```

---

## Phase 5: Post-Flight Analysis

### 5.1 Review Logs
```bash
# View flight log
ls -lt logs/
tail -100 logs/autonomous_flight_*.log

Look for:
□ Any errors or warnings
□ Safety alerts
□ Battery performance
□ GPS quality
□ Waypoint accuracy
```

### 5.2 Analyze Telemetry Data
```bash
# View telemetry CSV
head -20 logs/telemetry_*.csv

# Or import into Excel/Python for analysis
```

### 5.3 Checklist
```
Post-Flight:
□ Check battery condition
□ Inspect propellers for damage
□ Review flight logs
□ Document any issues
□ Note flight time and battery usage
□ Update flight logbook
```

---

## Emergency Procedures

### During Flight

**GPS Loss:**
- Vehicle will hold position or RTL
- Be ready to take manual control via RC

**Low Battery Alert:**
- System automatically initiates RTL
- Monitor landing location

**Geofence Breach:**
- System initiates RTL or LAND
- Check geofence settings

**System Error:**
- Press Ctrl+C to stop script
- Take manual control via RC
- Switch to STABILIZE mode
- Land manually

### Manual Override (ALWAYS AVAILABLE)
1. Flip RC mode switch to STABILIZE
2. Take manual control
3. Land safely
4. Investigate issue before next flight

---

## Troubleshooting Guide

### Connection Issues
```bash
# Check ArduPilot
ps aux | grep arducopter

# Check MAVLink
netstat -an | grep 14550

# Test connection
python3 src/utils/connection.py
```

### GPS Problems
```bash
# Monitor GPS status
python3 -c "
from src.utils.connection import VehicleConnection
conn = VehicleConnection()
vehicle = conn.connect()
gps = vehicle.gps_0
print(f'Fix: {gps.fix_type}, Sats: {gps.satellites_visible}')
conn.disconnect()
"

Solutions:
- Move to open area
- Wait 2-5 minutes
- Check GPS module connection
```

### Pre-Flight Check Failures
```bash
# Run detailed checks
python3 -c "
from src.autonomous_flight import AutonomousController
controller = AutonomousController()
controller.connect()
controller.safety.pre_flight_checks()
controller.disconnect()
"

# Check each system individually
```

---

## Safety Reminders

### Before EVERY Flight
- [ ] Clear airspace
- [ ] Battery charged
- [ ] RC transmitter ready
- [ ] GPS lock acquired
- [ ] Safety observer present
- [ ] Emergency plan ready

### During Flight
- [ ] Monitor telemetry continuously
- [ ] Keep RC in hand
- [ ] Maintain line of sight
- [ ] Watch for obstacles
- [ ] Check battery level

### After Flight
- [ ] Disarm motors
- [ ] Disconnect battery
- [ ] Review logs
- [ ] Inspect hardware
- [ ] Document flight

---

## Progressive Flight Testing Plan

### Week 1: Simulation
- [ ] Day 1-2: SITL setup and basic tests
- [ ] Day 3-4: Mission testing in SITL
- [ ] Day 5-7: Advanced scenarios

### Week 2: Real Flight - Basic
- [ ] Day 1: 2m hover, 10s
- [ ] Day 2: 5m hover, 20s
- [ ] Day 3: 10m hover, 30s
- [ ] Day 4-5: Altitude variations

### Week 3: Real Flight - Waypoints
- [ ] Day 1-2: 2-point missions
- [ ] Day 3-4: Square pattern
- [ ] Day 5-7: Complex patterns

### Week 4: Real Flight - Advanced
- [ ] Day 1-3: Survey missions
- [ ] Day 4-5: Variable altitude
- [ ] Day 6-7: Long-duration flights

---

## Quick Reference Commands

```bash
# Setup
./setup.sh

# Test connection
python3 src/utils/connection.py

# Monitor telemetry
python3 src/telemetry_monitor.py

# Simple test flight
python3 src/autonomous_flight.py --test --altitude 5 --duration 10

# Execute mission
python3 src/autonomous_flight.py --mission missions/simple_square.json

# Run examples
python3 examples.py

# Run tests
python3 -m pytest tests/

# View logs
tail -f logs/autonomous_flight_*.log
```

---

## Support Resources

- **Documentation**: README.md, QUICKSTART.md
- **Logs**: `logs/` directory
- **ArduPilot**: https://ardupilot.org/copter/
- **DroneKit**: https://dronekit-python.readthedocs.io/
- **Erle Robotics**: http://erlerobotics.com/docs/

---

**Remember: Safety is not optional. Follow all procedures. Start slow. Build confidence gradually. 🚁**
