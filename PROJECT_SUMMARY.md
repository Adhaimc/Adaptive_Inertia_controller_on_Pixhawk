# Erle-Brain 2 Autonomous Quadcopter Project

## 🚁 Project Overview

This is a complete autonomous flight system for Erle-Brain 2 flight controller using DroneKit-Python and ArduPilot.

### Features Implemented

✅ **Autonomous Flight Control**
- Automated takeoff and landing
- Waypoint navigation
- Return to launch (RTL)
- Multiple flight modes (GUIDED, AUTO, LOITER)

✅ **Safety Systems**
- Pre-flight safety checks (GPS, battery, sensors)
- Real-time battery monitoring
- Geofencing (horizontal and vertical)
- Emergency procedures
- Failsafe mechanisms

✅ **Mission Planning**
- JSON-based mission files
- Custom waypoint creation
- Variable altitude support
- Survey/mapping patterns

✅ **Telemetry & Monitoring**
- Real-time telemetry display
- CSV logging for analysis
- Flight data recording
- Console and file logging

✅ **Configuration Management**
- YAML-based configuration
- Adjustable parameters
- Safety limits
- Connection settings

## 📁 Project Structure

```
Erle_brain2/
├── README.md                  # Main documentation
├── QUICKSTART.md             # Quick start guide
├── LICENSE                   # MIT License
├── requirements.txt          # Python dependencies
├── setup.sh                  # Setup script
├── config/
│   └── flight_params.yaml    # Flight configuration
├── src/
│   ├── __init__.py
│   ├── autonomous_flight.py  # Main controller
│   ├── mission_planner.py    # Mission management
│   ├── safety_manager.py     # Safety checks
│   ├── telemetry_monitor.py  # Telemetry display
│   └── utils/
│       ├── __init__.py
│       ├── config.py         # Config management
│       ├── connection.py     # Vehicle connection
│       └── logger.py         # Logging utilities
├── missions/
│   ├── simple_square.json    # Square flight pattern
│   ├── waypoint_mission.json # Custom waypoints
│   └── survey_pattern.json   # Mapping pattern
├── tests/
│   ├── __init__.py
│   ├── test_config.py        # Config tests
│   └── test_safety_manager.py # Safety tests
└── logs/                     # Auto-generated logs
```

## 🚀 Quick Start

### 1. Installation

```bash
cd /Users/adhaimc/Documents/GitHub/Erle_brain2
./setup.sh
```

### 2. Configuration

Edit `config/flight_params.yaml`:
- Set connection string
- Configure safety parameters
- Adjust flight limits

### 3. Update Mission Coordinates

Edit mission files in `missions/` with your actual GPS location!

### 4. Test Connection

```bash
python3 src/utils/connection.py
```

### 5. Run Test Flight

**SIMULATION (Recommended First):**
```bash
# Start SITL on your computer
sim_vehicle.py --console --map

# Run test in simulation
python3 src/autonomous_flight.py --connection tcp:127.0.0.1:5760 --test
```

**REAL FLIGHT:**
```bash
# Simple hover test
python3 src/autonomous_flight.py --test --altitude 5 --duration 10

# Execute mission
python3 src/autonomous_flight.py --mission missions/simple_square.json
```

## 📋 Usage Examples

### Simple Test Flight
```bash
python3 src/autonomous_flight.py --test --altitude 10 --duration 20
```

### Waypoint Mission
```bash
python3 src/autonomous_flight.py --mission missions/waypoint_mission.json
```

### Monitor Telemetry
```bash
python3 src/telemetry_monitor.py
```

### Test Connection
```bash
python3 src/utils/connection.py
```

## 🛡️ Safety Features

1. **Pre-Flight Checks**
   - GPS lock verification (6+ satellites)
   - Battery level check
   - Sensor health verification
   - Home position confirmation

2. **In-Flight Monitoring**
   - Continuous battery monitoring
   - Geofence enforcement
   - GPS quality tracking
   - Real-time telemetry

3. **Emergency Procedures**
   - Automatic RTL on low battery
   - Geofence breach handling
   - GPS loss failsafe
   - Manual RC override always available

## 🎯 Mission Planning

### Create Custom Mission

Edit `missions/waypoint_mission.json`:

```json
{
  "name": "My Mission",
  "waypoints": [
    {"lat": 37.7749, "lon": -122.4194, "alt": 10.0},
    {"lat": 37.7750, "lon": -122.4195, "alt": 15.0}
  ]
}
```

### Mission Types Included

1. **Simple Square** - Basic square pattern
2. **Waypoint Mission** - Multi-point with variable altitude
3. **Survey Pattern** - Lawn-mower pattern for mapping

## 📊 Telemetry & Logging

### Real-time Telemetry
- Position (GPS coordinates, altitude)
- Velocity (ground speed, air speed)
- Attitude (roll, pitch, yaw)
- Battery (voltage, current, level)
- GPS (fix type, satellites, HDOP)

### Log Files
- Flight logs: `logs/autonomous_flight_*.log`
- Telemetry CSV: `logs/telemetry_*.csv`

## 🧪 Testing

```bash
# Run unit tests
python3 -m pytest tests/

# Test individual components
python3 src/utils/connection.py
python3 src/telemetry_monitor.py
```

## ⚙️ Configuration

Key settings in `config/flight_params.yaml`:

```yaml
flight:
  max_altitude: 50.0        # Maximum flight altitude
  default_speed: 5.0        # Default speed (m/s)
  
safety:
  battery_critical: 10.5    # Critical voltage (RTL)
  gps_min_satellites: 6     # Minimum satellites
  
geofence:
  radius: 100.0             # Fence radius (m)
  max_altitude: 50.0        # Max altitude (m)
```

## 🔧 Troubleshooting

### Connection Failed
- Check ArduPilot is running: `ps aux | grep arducopter`
- Verify MAVLink port: `netstat -an | grep 14550`
- Check connection string in config

### Pre-flight Checks Failed
- Wait for GPS lock (outdoors, clear sky)
- Check battery voltage
- Verify all sensors are working

### GPS Issues
- Ensure clear view of sky
- Wait 1-2 minutes for fix
- Check GPS module connection

## 📚 Documentation

- `README.md` - Main documentation
- `QUICKSTART.md` - Step-by-step guide
- Code comments - Detailed in-line documentation
- ArduPilot docs: https://ardupilot.org/copter/
- DroneKit docs: https://dronekit-python.readthedocs.io/

## ⚠️ SAFETY WARNINGS

**CRITICAL - READ BEFORE FLYING:**

1. ✋ **Always test in simulation first** (SITL)
2. 👥 **Never fly near people or buildings**
3. 🎮 **Keep RC transmitter ready for manual override**
4. 👀 **Maintain visual line of sight**
5. 📋 **Follow local aviation regulations**
6. 🔋 **Check battery before every flight**
7. 🌤️ **Only fly in good weather conditions**
8. 🚁 **Start with low altitude (2-5m)**

## 🤝 Contributing

Contributions welcome! Please:
1. Test in SITL first
2. Include documentation
3. Add unit tests
4. Follow code style

## 📄 License

MIT License - See LICENSE file

**Safety Disclaimer:** Use at your own risk. Authors not liable for damages.

## 🙏 Acknowledgments

- ArduPilot Development Team
- DroneKit Development Team
- Erle Robotics
- Open source drone community

## 📧 Support

- Check logs for errors
- Review ArduPilot documentation
- Test components individually
- Use telemetry monitor for debugging

---

## Next Steps

1. ✅ Complete setup: `./setup.sh`
2. ✅ Read `QUICKSTART.md` thoroughly
3. ✅ Configure `config/flight_params.yaml`
4. ✅ Update mission GPS coordinates
5. ✅ Test in SITL simulation
6. ✅ Test connection to Erle-Brain 2
7. ✅ Monitor telemetry
8. ✅ Run simple test flight (low altitude)
9. ✅ Execute missions gradually
10. ✅ Review logs after each flight

**Remember: Safety First, Always! 🚁**
