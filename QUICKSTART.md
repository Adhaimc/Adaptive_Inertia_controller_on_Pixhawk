# Erle-Brain 2 Autonomous Flight - Quick Start Guide

## Step 1: Hardware Setup

1. **Connect Erle-Brain 2 to your quadcopter:**
   - Install Erle-Brain 2 on your frame
   - Connect ESCs to motor outputs
   - Connect RC receiver (optional but recommended for safety)
   - Connect GPS module
   - Connect battery with voltage monitoring

2. **Power on and connect:**
   ```bash
   # Via WiFi
   ssh erle@erle-brain-2.local
   # Password: holaerle
   
   # Or via Ethernet (check IP with nmap)
   ssh erle@192.168.x.x
   ```

## Step 2: Software Installation

```bash
# On Erle-Brain 2
cd ~
git clone <your-repo-url> Erle_brain2
cd Erle_brain2

# Install Python dependencies
pip3 install -r requirements.txt

# Verify ArduPilot is running
ps aux | grep arducopter
```

## Step 3: Configuration

1. **Edit flight parameters:**
   ```bash
   nano config/flight_params.yaml
   ```

2. **Important settings to check:**
   - Connection string (default: `udp:127.0.0.1:14550`)
   - Flight altitude limits
   - Battery voltage thresholds
   - Geofence parameters (radius, max altitude)
   - GPS requirements

3. **Update mission coordinates:**
   ```bash
   nano missions/simple_square.json
   ```
   Replace example coordinates with your actual GPS location!

## Step 4: Test Connection

```bash
# Test vehicle connection
python3 src/utils/connection.py

# Should show:
# ✓ Connection successful!
# Vehicle Status: Armed: False, Mode: GUIDED, etc.
```

## Step 5: Monitor Telemetry

```bash
# Monitor real-time telemetry
python3 src/telemetry_monitor.py

# You should see live data:
# - Position (lat/lon/alt)
# - Velocity and speed
# - Battery voltage
# - GPS satellites
# - Flight mode
```

## Step 6: Pre-Flight Checklist

**CRITICAL - Do this every time before flight:**

- [ ] Battery fully charged (check voltage)
- [ ] GPS lock with 6+ satellites
- [ ] Clear airspace - no obstacles
- [ ] RC transmitter ready (for manual override)
- [ ] Geofence configured correctly
- [ ] Home position set
- [ ] Mission coordinates verified
- [ ] Safety observer present

## Step 7: First Test Flight (SIMULATION RECOMMENDED)

**Option A: SITL Simulation (Recommended First)**

```bash
# On your computer, install ArduPilot SITL
cd ~/
git clone https://github.com/ArduPilot/ardupilot
cd ardupilot
git submodule update --init --recursive

# Start simulator
cd ArduCopter
sim_vehicle.py --console --map

# In another terminal, run test flight
python3 src/autonomous_flight.py \
  --connection tcp:127.0.0.1:5760 \
  --test \
  --altitude 10 \
  --duration 10
```

**Option B: Real Flight (After simulation success)**

```bash
# Simple test flight: takeoff, hover 10s, land
python3 src/autonomous_flight.py \
  --test \
  --altitude 5 \
  --duration 10

# Monitor in another terminal
python3 src/telemetry_monitor.py
```

## Step 8: Execute Mission

```bash
# Run pre-defined square pattern
python3 src/autonomous_flight.py \
  --mission missions/simple_square.json

# Or custom waypoint mission
python3 src/autonomous_flight.py \
  --mission missions/waypoint_mission.json
```

## Emergency Procedures

### Manual Override
- **RC transmitter can ALWAYS take control**
- Switch to STABILIZE or LOITER mode on RC
- Take manual control if anything goes wrong

### Emergency Stop
- Press `Ctrl+C` to interrupt script
- Vehicle will attempt emergency landing
- RC override is still available

### Battery Low
- System monitors battery automatically
- Returns to launch when critical
- Always land if voltage drops below 10.5V

### GPS Loss
- Vehicle will attempt to hold position
- If prolonged, will initiate emergency landing
- Do not fly in areas with poor GPS

## Troubleshooting

### "Failed to connect to vehicle"
```bash
# Check ArduPilot is running
ps aux | grep arducopter

# Check MAVLink port
netstat -an | grep 14550

# Verify connection string in config
cat config/flight_params.yaml | grep connection
```

### "Pre-flight checks failed"
- Check GPS lock (may need to wait 1-2 minutes outdoors)
- Verify battery voltage
- Ensure ArduPilot parameters are set
- Check RC connection if required

### "Vehicle not armable"
- Ensure GPS has 3D fix
- Check all sensors are calibrated
- Verify flight mode is GUIDED
- Review ArduPilot pre-arm messages

## Next Steps

1. **Test in simulation extensively**
2. **Start with low altitudes (2-5m)**
3. **Gradually increase complexity**
4. **Always have safety observer**
5. **Review logs after each flight**

## Log Files

All flights are logged:
```bash
# View flight logs
ls -lh logs/

# Check latest log
tail -f logs/autonomous_flight_*.log

# Review telemetry CSV
cat logs/telemetry_*.csv
```

## Safety Reminders

⚠️ **CRITICAL SAFETY RULES** ⚠️

1. **Always test in simulation first**
2. **Never fly near people or buildings**
3. **Keep RC transmitter ready**
4. **Maintain visual line of sight**
5. **Follow local regulations**
6. **Have emergency landing plan**
7. **Start with low altitude**
8. **Check weather conditions**

## Support

- Check logs for error messages
- Review ArduPilot documentation
- Test individual components (GPS, battery, etc.)
- Use telemetry monitor to diagnose issues

## Happy Flying! 🚁

Remember: **Safety First, Always!**
