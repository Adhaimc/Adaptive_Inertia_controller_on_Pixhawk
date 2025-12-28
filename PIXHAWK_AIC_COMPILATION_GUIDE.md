# Pixhawk 2.4.8 AIC Module Compilation Guide

For advanced users who want to compile **custom ArduCopter with AIC module** instead of using pre-built firmware.

⚠️ **Prerequisites:**
- Linux or macOS machine
- Git, Python 3.7+
- 2-3 hours setup time
- Familiar with command line

---

## Quick Start (Impatient Path)

**Skip this guide if:**
- You're OK using standard ArduCopter 4.4.2 (AIC not needed for first flight)
- You want stable flight quickly (standard firmware = safe + proven)
- You're doing first-time migration (save AIC compilation for later)

**Use this guide if:**
- You have a Pixhawk and want native AIC integration
- You understand ArduPilot codebase
- You're willing to debug compilation issues

---

## Option 1: Easiest (Recommended for First Flight)

**Use standard pre-built ArduCopter:**

Your Python code will work without any C++ compilation:
```bash
# Just update connection parameters, fly with default control
pip install -r requirements.txt

# Will work fine with out-of-the-box ArduCopter 4.4.2
python src/autonomous_flight.py
```

✅ **Advantages:**
- No compilation needed
- Proven stable firmware
- Can tune AIC parameters via Python after
- Works immediately

❌ **Disadvantages:**
- Can't modify C++ control law
- Uses stock ArduCopter attitude controller

---

## Option 2: Compile Custom ArduCopter with AIC

### Step 1: Set Up Build Environment

#### macOS Setup

```bash
# Install Xcode command-line tools
xcode-select --install

# Install Python 3.7+ (if not present)
brew install python3 python3-dev

# Install build tools
brew install gcc g++ pip git

# Install required Python packages for ArduPilot
pip3 install cython pexpect empy numpy

# Verify Python 3
python3 --version  # Should be 3.7 or higher
```

#### Linux Setup (Ubuntu/Debian)

```bash
# Update package lists
sudo apt-get update
sudo apt-get upgrade

# Install build tools and dependencies
sudo apt-get install -y \
    git \
    gcc \
    g++ \
    make \
    cmake \
    python3 \
    python3-dev \
    python3-pip \
    libpython3-dev

# Install Python packages
pip3 install cython pexpect empy numpy

# Add yourself to dialout group for USB access
sudo usermod -a -G dialout $USER
```

### Step 2: Clone ArduPilot Repository

```bash
# Choose a working directory
cd ~/development  # or wherever you keep projects

# Clone ArduPilot main repository
git clone https://github.com/ArduPilot/ardupilot.git
cd ardupilot

# Checkout stable 4.4.2 branch
git checkout Copter-4.4.2

# Initialize submodules
git submodule update --init --recursive

# Verify directory structure
ls -la modules/  # Should see many module directories
```

### Step 3: Copy Your AIC Module

```bash
# From your Erle_brain2 project:
# Copy the entire attitude_controller_aic module

# Option A: If in same directory as ardupilot
cp -r ../Erle_brain2/src/modules/attitude_controller_aic \
      ardupilot/modules/

# Option B: Manual copy
# Navigate to: ardupilot/modules/attitude_controller_aic/
# Place these files:
# - AttitudeControllerAIC.cpp
# - CMakeLists.txt
# - include/
#   - attitude_controller_aic.hpp
#   - iwg_adapter.hpp
#   - regressor.hpp
#   - so3_utils.hpp
#   - adaptive_estimator.hpp

# Verify structure
ls -la modules/attitude_controller_aic/include/
# Should see all .hpp files
```

### Step 4: Update CMakeLists.txt

**File:** `ardupilot/modules/attitude_controller_aic/CMakeLists.txt`

For ArduPilot builds, ensure it uses ArduPilot's matrix library:

```cmake
# ArduPilot CMakeLists.txt format

# Find the ArduPilot matrix library
find_package(MATRIX REQUIRED)

# Add the module as a library
add_library(attitude_controller_aic STATIC
    AttitudeControllerAIC.cpp
)

# Include directories
target_include_directories(attitude_controller_aic PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${MATRIX_INCLUDE_DIRS}
)

# Link ArduPilot libraries
target_link_libraries(attitude_controller_aic
    PRIVATE
    ${MATRIX_LIBRARIES}
)
```

Alternatively, if standard CMakeLists doesn't exist, ArduPilot uses `waf` build system. Create:

**File:** `ardupilot/modules/attitude_controller_aic/wscript`

```python
def build(bld):
    bld(
        features='cxx cxxstlib',
        name='attitude_controller_aic',
        source=[
            'AttitudeControllerAIC.cpp',
        ],
        includes=[
            '.',
            'include',
        ],
        use=[
            'AP_HAL',
            'AP_AHRS',
            'AP_Math',
        ],
        target='attitude_controller_aic',
    )
```

### Step 5: Verify Header Dependencies

Check that `AttitudeControllerAIC.cpp` includes correct ArduPilot headers:

```cpp
// Should include (examples):
#include <AP_AHRS/AP_AHRS.h>
#include <AP_Math/AP_Math.h>
#include <AP_Motors/AP_Motors.h>

// Your custom headers:
#include "attitude_controller_aic.hpp"
#include "so3_utils.hpp"
#include "regressor.hpp"
#include "iwg_adapter.hpp"
```

### Step 6: Configure Build

```bash
cd ~/development/ardupilot

# Configure for Pixhawk 2.4.8 (same as PX4 FMU v3)
./waf configure --board pixhawk

# If successful, you'll see:
# "Configuring ardupilot..."
# "[lots of output]"
# "Build dir: build/pixhawk"
```

**If configure fails:**
```
Common issues:
1. Python 3.7+ not found
   → pip3 install --upgrade pip setuptools

2. Missing build tools
   → macOS: xcode-select --install
   → Linux: sudo apt-get install build-essential

3. Submodules not initialized
   → git submodule update --init --recursive
```

### Step 7: Compile Copter Firmware

```bash
# Build (takes 3-10 minutes depending on machine)
./waf copter --jobs 4

# Watch for:
# - No red "error:" lines (warnings ok)
# - "Build finished successfully"

# Output file location:
# build/pixhawk/bin/arducopter
```

**If compilation fails:**

```bash
# Try clean rebuild
./waf clean
./waf copter --jobs 1  # Single job for better error messages

# Or check specific module:
./waf build --targets attitude_controller_aic
```

### Step 8: Upload Firmware to Pixhawk

#### Option A: Direct USB Upload

```bash
# Connect Pixhawk via USB

# Identify port
ls /dev/cu.usb*           # macOS
ls /dev/ttyUSB*           # Linux

# Upload (replace port as needed)
./waf copter --upload --port=/dev/cu.usbmodem14101

# Watch for:
# "Loaded firmware in 0.xx seconds"
# "Program sent!" 
# Pixhawk reboots with new firmware
```

#### Option B: Via Ground Station

```bash
# Copy compiled binary
cp build/pixhawk/bin/arducopter ~/Downloads/

# Open Mission Planner / QGroundControl
# Initial Setup → Firmware → Load Custom Firmware → Select the binary
# Wait for upload and reboot
```

### Step 9: Verify Firmware Loaded

```bash
# After upload, Pixhawk should boot
# Watch for:
# - Solid green light (ready)
# - No red light (no errors)

# Test connection
mavproxy.py --master=/dev/ttyUSB0 --baudrate=115200

# In MAVProxy, check:
# "HEARTBEAT {type : Quadrotor X, autopilot : ArduPilot, ...}"

# Exit with: Ctrl+C
```

### Step 10: Configure AIC Module Parameters

Once firmware uploaded, configure in Mission Planner:

```
Initial Setup → Parameters → Search "AIC"

Set:
- AIC_ENABLE: 1 (enable module)
- AIC_IMON_XX, YY, ZZ: Your measured inertia
- AIC_KR_*: Control gains
- AIC_KOMEGA_*: Rate gains
```

(Parameter naming depends on AttitudeControllerAIC.cpp implementation)

---

## Troubleshooting Compilation

### "ModuleNotFoundError: No module named 'empy'"

```bash
pip3 install empy cython pexpect
```

### "error: 'matrix::Vector3f' was not declared"

Missing include path or incompatible matrix library version.

**Fix:**
```cpp
// In AttitudeControllerAIC.cpp, ensure:
#include <matrix/matrix.hpp>  // ArduPilot matrix library
// NOT your own matrix definitions
```

### "ld.so.1: arducopter: fatal: libarpc.so.1: cannot open"

ArduPilot library incompatibility. Try:

```bash
./waf clean
./waf copter --strict-checks --jobs 1
```

### Build Takes Hours / Freezes

Likely out of memory. Try:

```bash
./waf copter --jobs 1  # Serial build instead of parallel
# Or increase system swap:
# Linux: sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile
```

---

## Validation Steps

After successful upload:

### 1. Verify Module Loaded

```bash
mavproxy.py --master=/dev/ttyUSB0 --baudrate=115200

# In MAVProxy terminal:
param fetch AIC_ENABLE
# Should return: AIC_ENABLE = 1 (if module implements this)

exit
```

### 2. Bench Test (No Props)

```bash
# Arm Pixhawk (via RC stick combination)
# In Mission Planner Motor Test:
# Test each motor to verify AIC isn't interfering
# Motors should spin smoothly
```

### 3. First Flight Test

```bash
# Follow steps in PIXHAWK_QUICK_START.md
# AIC controller should activate automatically
# Monitor logs for control performance
```

---

## File Checklist

Verify these files exist before compilation:

```bash
ardupilot/
├── modules/attitude_controller_aic/
│   ├── AttitudeControllerAIC.cpp          ✓
│   ├── CMakeLists.txt (or wscript)        ✓
│   └── include/
│       ├── attitude_controller_aic.hpp    ✓
│       ├── iwg_adapter.hpp                ✓
│       ├── regressor.hpp                  ✓
│       ├── so3_utils.hpp                  ✓
│       └── adaptive_estimator.hpp         ✓
```

---

## Reference: ArduPilot Build System

**For integrating AIC into other boards:**

```bash
# List supported boards
./waf list_boards

# For Pixhawk 2.4.8:
./waf configure --board pixhawk

# For PX4 FMU v5:
./waf configure --board px4-v5

# For Pixracer:
./waf configure --board pixracer

# Other options:
./waf configure --help
```

---

## When to Use Pre-Built vs Custom

| Scenario | Use Pre-Built | Use Custom |
|----------|--------------|-----------|
| First flight | ✅ Yes | ❌ No |
| Testing Python autonomy | ✅ Yes | ❌ No |
| Custom attitude control law | ❌ No | ✅ Yes |
| Advanced AIC tuning | ❌ No | ✅ Yes |
| Modifying C++ firmware | ❌ No | ✅ Yes |

---

## Next Steps After Compilation

1. ✅ Firmware uploaded to Pixhawk
2. ✅ Follow PIXHAWK_QUICK_START.md calibration steps
3. ✅ Test flight in STABILIZE mode
4. ✅ Review logs and tune AIC parameters
5. ✅ Progressive gain increases over multiple flights

---

## Support & Documentation

- **ArduPilot Building from Source:** https://ardupilot.org/dev/docs/building-the-code.html
- **Pixhawk Setup Guide:** https://ardupilot.org/copter/docs/pixhawk-setup-v1-2.html
- **ArduCopter Configuration:** https://ardupilot.org/copter/docs/configuration.html
- **Your AIC Module Documentation:** See `IMPLEMENTATION_GUIDE_AIC.md`

---

**If compilation works, you've successfully integrated AIC with Pixhawk 2.4.8!** 🎉

If you hit issues, start with pre-built firmware and circle back to custom compilation after first flight succeeds.
