# Erle-Brain 2 Autonomous Quadcopter Flight

A comprehensive Python-based autonomous flight system for quadcopters using Erle-Brain 2 flight controller with ArduPilot and DroneKit.

## Features

- ✈️ Fully autonomous waypoint navigation
- 🛡️ Safety features (geofencing, battery monitoring, failsafes)
- 📊 Real-time telemetry and logging
- 🎯 Multiple flight modes (guided, auto, loiter)
- 🔄 Automatic takeoff and landing
- 📡 MAVLink communication
- 🗺️ Mission planning and execution
- 🎮 Manual override capability

## Project Structure

```
Erle_brain2/
├── src/
│   ├── autonomous_flight.py      # Main autonomous flight controller
│   ├── mission_planner.py        # Mission planning and waypoint management
│   ├── telemetry_monitor.py      # Real-time telemetry monitoring
│   ├── safety_manager.py         # Safety checks and failsafes
│   └── utils/
│       ├── connection.py         # Vehicle connection utilities
│       ├── logger.py             # Flight data logging
│       └── config.py             # Configuration management
├── missions/
│   ├── simple_square.json        # Example: Square pattern flight
│   ├── waypoint_mission.json     # Example: Custom waypoint mission
│   └── survey_pattern.json       # Example: Survey/mapping pattern
├── config/
│   └── flight_params.yaml        # Flight parameters configuration
├── logs/                         # Flight logs directory
├── tests/                        # Unit tests
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## Hardware Requirements

- Erle-Brain 2 flight controller
- Quadcopter frame with motors and ESCs
- RC transmitter and receiver
- Battery with voltage monitoring
- GPS module (usually integrated)
- Optional: Companion computer or WiFi connection

## Software Requirements

- Python 3.7+
- DroneKit-Python
- pymavlink
- ArduPilot firmware (ArduCopter)

## Installation

### On Erle-Brain 2:

```bash
# SSH into Erle-Brain 2
ssh erle@erle-brain-2.local
# Password: holaerle

# Update system
sudo apt-get update
sudo apt-get upgrade

# Install Python dependencies
sudo apt-get install python3-pip python3-dev
sudo pip3 install dronekit pymavlink pyyaml

# Clone this repository
git clone <your-repo-url>
cd Erle_brain2

# Install project dependencies
pip3 install -r requirements.txt
```

### On Development Computer (for simulation/testing):

```bash
# Install dependencies
pip install -r requirements.txt

# Install MAVProxy for simulation
pip install MAVProxy

# For SITL (Software In The Loop) testing
git clone https://github.com/ArduPilot/ardupilot
cd ardupilot
git submodule update --init --recursive
```

## Quick Start

### 1. Basic Connection Test

```bash
python3 src/utils/connection.py
```

### 2. Monitor Telemetry

```bash
python3 src/telemetry_monitor.py
```

### 3. Run Autonomous Mission

```bash
# Run a pre-defined mission
python3 src/autonomous_flight.py --mission missions/simple_square.json

# Run with custom parameters
python3 src/autonomous_flight.py --mission missions/waypoint_mission.json --altitude 10 --speed 5
```

## Configuration

Edit `config/flight_params.yaml` to customize:

- Flight altitude and speed limits
- Geofencing boundaries
- Battery thresholds
- Safety parameters
- Connection settings

## Safety Features

1. **Pre-flight Checks**: GPS lock, battery level, sensor status
2. **Geofencing**: Prevents flight outside defined boundaries
3. **Battery Monitoring**: Auto-return on low battery
4. **GPS Quality Check**: Ensures sufficient satellite lock
5. **Manual Override**: RC transmitter can always override
6. **Emergency Landing**: Triggered on critical failures

## Usage Examples

### Simple Takeoff and Land

```python
from src.autonomous_flight import AutonomousController

controller = AutonomousController(connection_string='udp:127.0.0.1:14550')
controller.connect()
controller.arm_and_takeoff(10)  # Takeoff to 10 meters
time.sleep(10)  # Hover for 10 seconds
controller.land()
```

### Waypoint Mission

```python
from src.mission_planner import MissionPlanner

planner = MissionPlanner(connection_string='udp:127.0.0.1:14550')
planner.load_mission('missions/waypoint_mission.json')
planner.execute_mission()
```

## Connection Strings

- **Erle-Brain 2 Local**: `udp:127.0.0.1:14550`
- **Erle-Brain 2 via WiFi**: `udp:<erle-brain-ip>:14550`
- **Serial Connection**: `/dev/ttyAMA0` (baud: 57600 or 921600)
- **SITL Simulation**: `tcp:127.0.0.1:5760`

## Testing

### Run Unit Tests

```bash
python3 -m pytest tests/
```

### Simulation Testing (SITL)

```bash
# Start SITL simulator
cd ardupilot/ArduCopter
sim_vehicle.py --console --map

# In another terminal, run your script
python3 src/autonomous_flight.py --connection tcp:127.0.0.1:5760
```

## Troubleshooting

### Connection Issues
- Check if ArduPilot is running: `ps aux | grep arducopter`
- Verify MAVLink port: `netstat -an | grep 14550`
- Check WiFi connection to Erle-Brain 2

### GPS Problems
- Ensure clear sky view
- Wait for GPS lock (3D fix with 6+ satellites)
- Check GPS module connection

### Arming Issues
- Verify all pre-arm checks pass
- Check RC calibration
- Ensure flight mode is correct (GUIDED or AUTO)

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Test thoroughly (preferably in SITL first)
4. Submit a pull request

## Safety Warning

⚠️ **IMPORTANT SAFETY NOTICE** ⚠️

- Always test in SITL simulation first
- Follow local aviation regulations
- Keep RC transmitter ready for manual override
- Never fly near people, buildings, or airports
- Always maintain visual line of sight
- Start with low altitude and slow speed
- Have emergency landing procedures ready

## Resources

- [ArduPilot Documentation](https://ardupilot.org/copter/)
- [DroneKit-Python Documentation](https://dronekit-python.readthedocs.io/)
- [Erle-Brain 2 Documentation](http://erlerobotics.com/docs/)
- [MAVLink Protocol](https://mavlink.io/en/)

## License

MIT License - See LICENSE file for details

## Authors

- Your Name

## Acknowledgments

- ArduPilot Development Team
- DroneKit Development Team
- Erle Robotics
