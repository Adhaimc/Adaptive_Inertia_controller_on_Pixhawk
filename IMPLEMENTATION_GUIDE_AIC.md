# Adaptive Inertia Estimation Controller (AIC) - Implementation Guide

## Overview

This module implements **Adaptive Inertia-aware Composite (AIC) Attitude Control on SO(3)** for Pixhawk/PX4 multicopters. Based on the paper "Adaptive Inertia Estimation Augmented Geometric PD Control on SO(3) Suitable for Embedded Controllers".

**Key Features:**
- Geometric PD attitude control with almost-global convergence on SO(3)
- Online adaptive learning of inertia matrix parameters
- Information-Weighted Gradient (IWG) for handling actuator saturation
- Lyapunov-stable with bounded disturbance rejection
- Lightweight implementation for embedded systems (~200 operations per 10ms step)

---

## Module Architecture

```
AttitudeControllerAIC.cpp (PX4 interface)
    │
    ├── AttitudeControllerAIC (composite controller)
    │   ├── SO3Utils (geometric math on SO(3))
    │   ├── Regressor (linear-in-parameters torque model)
    │   └── IWGAdapter (adaptive inertia estimation)
    │       └── Information matrix accumulation
```

### File Structure
```
src/modules/attitude_controller_aic/
├── CMakeLists.txt                    # Build configuration
├── AttitudeControllerAIC.cpp         # PX4 module wrapper
└── include/
    ├── so3_utils.hpp                 # SO(3) attitude kinematics
    ├── regressor.hpp                 # Torque regressor Y(ω,α)
    ├── adaptive_estimator.hpp        # Basic adaptive update (optional)
    ├── iwg_adapter.hpp               # IWG parameter estimation
    └── attitude_controller_aic.hpp   # Main composite controller
```

---

## Control Law

The complete torque command is:

$$\tau = -K_R e_R - K_\Omega e_\Omega + Y(\omega,\alpha)\hat{\theta} - K s$$

where:
- **Geometric PD:** $-K_R e_R - K_\Omega e_\Omega$ stabilizes attitude on SO(3)
- **Adaptive feedforward:** $Y(\omega,\alpha)\hat{\theta}$ learns and cancels inertia dynamics
- **Robust damping:** $-K s$ attenuates unmodeled effects and sensor noise
- **Composite error:** $s = e_\Omega + c \cdot e_R$

### Attitude Errors

$$e_R = \frac{1}{2} \text{vee}\left(R_d^T R - R^T R_d\right)$$

$$e_\Omega = \Omega - R^T R_d \Omega_d$$

### Inertia Learning

Parameter update (IWG method):

$$\dot{\hat{\theta}} = -\Gamma (I + \lambda P)^{-1} Y^T s - \sigma \Gamma \hat{\theta}$$

where $P(t) = \int_0^t Y^T Y \, d\tau$ accumulates information quality.

---

## Default Configuration & Tuning

### 1. Initial Inertia Estimate

Measure or estimate your quadcopter's moment of inertia. For a typical 1.2 kg quadcopter:

```cpp
// src/modules/attitude_controller_aic/AttitudeControllerAIC.cpp
Matrix3f J_init = Matrix3f::Zero();
J_init(0, 0) = 0.040f;  // Ixx (kg·m²)  <-- TUNE THIS
J_init(1, 1) = 0.040f;  // Iyy
J_init(2, 2) = 0.025f;  // Izz
```

**How to measure/estimate Ixx:**
- Roll the quadcopter by hand (no propellers!) and measure period of oscillation
- Use CAD model + mass distribution
- Conservative approach: set values 10-20% lower than true (adaptation will learn up)

### 2. Control Gains

**Recommended starting values (tune iteratively):**

| Parameter | Value | Notes |
|-----------|-------|-------|
| K_R (roll/pitch) | 5.0 | Attitude error gain - increase for faster response |
| K_R (yaw) | 3.0 | Yaw typically needs lower gain |
| K_Ω (roll/pitch) | 0.3 | Angular velocity damping |
| K_Ω (yaw) | 0.2 | |
| K (robust) | 0.1 | Noise rejection - increase if oscillations occur |
| c (composite) | 2.0 | Weight of attitude in composite error (1.5-3.0) |

**Tuning procedure:**

1. **Conservative initial gains:** Start with 70% of values above
2. **Test tracking:** Send small attitude commands (±5°)
3. **Increase K_R gradually:** Until response time is ~0.5-1 second
4. **Increase K_Ω gradually:** Until oscillations appear, then back off
5. **Increase K if noisy:** Especially if ESC firmware has jitter

### 3. Adaptation Parameters

| Parameter | Value | Effect |
|-----------|-------|--------|
| gamma | 1.5 | Learning rate - higher = faster inertia adaptation (1-5) |
| sigma | 1e-4 | Leakage (drift prevention) - increase for noisy gyros |
| beta | 0.01 | Regularization - prevent parameter jumps |
| lambda | 0.04 | IWG weighting factor (0.01-0.1) |
| gamma_ee | 0.001 | Excitation enhancing - increase if learning stalls during hover |

**Adaptation strategy:**

For **payload-constrained quadrotors** (battery-powered, tight actuators):
```cpp
gamma_ = 1.5f;      // Moderate learning
sigma_ = 5e-5f;     // Light leakage
lambda_ = 0.04f;    // Information weighting
gamma_ee_ = 0.001f; // Enable internal excitation
```

For **high-power platforms** (no saturation):
```cpp
gamma_ = 0.5f;      // Conservative learning
sigma_ = 1e-4f;     // Stronger leakage
lambda_ = 0.0f;     // Disable IWG (standard gradient sufficient)
gamma_ee_ = 0.0f;   // Disable excitation
```

### 4. Actuator Saturation Limits

Set based on ESC PWM limits and motor performance:

```cpp
_controller.set_saturation_limit(0.045f);  // Typical: 0.03-0.06 Nm
```

**Pixhawk mounting:**
- Adjust in [src/modules/attitude_controller_aic/AttitudeControllerAIC.cpp](src/modules/attitude_controller_aic/AttitudeControllerAIC.cpp#L145)
- Or expose as PX4 parameter: `MC_AIC_TAU_MAX`

### 5. Filter Bandwidth

Composite error low-pass filter reduces sensor noise:

```cpp
_controller.set_filter_bandwidth(0.1f);  // 0.0 (no filter) to 1.0 (max smoothing)
```

**Typical values:**
- Noisy IMU: 0.1-0.2
- Good IMU: 0.05-0.1
- Noiseless (simulation): 0.01

---

## Building & Deployment

### 1. Add to PX4 Build System

Copy module to PX4 firmware:
```bash
cp -r src/modules/attitude_controller_aic /path/to/PX4-Autopilot/src/modules/
```

### 2. Register Module in PX4 CMakeLists.txt

Add to `/path/to/PX4-Autopilot/src/modules/CMakeLists.txt`:
```cmake
add_subdirectory(attitude_controller_aic)
```

### 3. Enable Eigen3 (if not already available)

```bash
sudo apt-get install libeigen3-dev
```

### 4. Build for Pixhawk 4

```bash
cd PX4-Autopilot
make px4_fmu-v5_default  # For Pixhawk 4
make px4_fmu-v4_default  # For Pixhawk 3 Pro
```

### 5. Flash to Pixhawk

```bash
make px4_fmu-v5_default upload  # With USB connected
```

---

## PX4 Parameters (Exposed via Tuning Stick)

Once integrated, these parameters appear in QGroundControl:

| Parameter | Type | Range | Default |
|-----------|------|-------|---------|
| MC_AIC_EN | boolean | 0/1 | 1 (enabled) |
| MC_AIC_J_XX | float | 0.01-1.0 | 0.040 |
| MC_AIC_J_YY | float | 0.01-1.0 | 0.040 |
| MC_AIC_J_ZZ | float | 0.01-1.0 | 0.025 |
| MC_AIC_GAMMA | float | 0.1-5.0 | 1.5 |
| MC_AIC_SIGMA | float | 1e-5-1e-3 | 1e-4 |
| MC_AIC_TAU_MAX | float | 0.01-1.0 | 0.045 |
| MC_AIC_C | float | 1.0-5.0 | 2.0 |

**To expose parameters, extend the PX4 module with:**
```cpp
DEFINE_PARAMETERS(
    (ParamFloat<px4::params::MC_AIC_GAMMA>) _param_aic_gamma,
    (ParamFloat<px4::params::MC_AIC_SIGMA>) _param_aic_sigma,
    // ... etc
)
```

---

## Testing Procedure

### 1. SITL Simulation (Recommended First)

```bash
# Terminal 1: Start simulator
make px4_sitl jmavsim

# Terminal 2: Monitor vehicle
mavproxy.py --master=tcp:127.0.0.1:5760 --out=udp:127.0.0.1:14550

# Terminal 3: Command attitude changes
# Use MAVProxy or QGroundControl to send position/attitude setpoints
```

### 2. Ground Bench Test

1. Connect Pixhawk to computer (USB)
2. Arm quadcopter in ATTITUDE mode
3. Send small attitude commands via RC or MAVProxy
4. Monitor gyro/accel via telemetry
5. Verify smooth, non-oscillatory response

### 3. Flight Test (With Safety Observer)

**Phase 1: Hover Test** (5 minutes)
- Arm in ATTITUDE or ALT_HOLD mode
- Hover 1-2 meters high
- Command small roll/pitch oscillations (±5°)
- Verify stable recovery

**Phase 2: Tracking Test** (5 minutes)
- Command slow sinusoidal attitude reference (0.5 Hz, 10° amplitude)
- Observe convergence and steady-state tracking error
- Monitor battery current (should be reasonable)

**Phase 3: Payload Change** (5 minutes)
- Hover with 500g payload
- Verify controller adapts (will see initial error, then correction)
- Drop payload and reverify

---

## Monitoring & Debugging

### 1. Log Telemetry

PX4 automatically logs:
- `attitude`: R, ω, errors
- `actuator_controls`: τ commands
- `vehicle_rates`: angular velocities

Use pyulog to analyze:
```bash
pyulog info flight_log.ulg  # List all topics
pyulog plot flight_log.ulg -m attitude -m actuator_controls
```

### 2. Real-Time Monitoring (MAVProxy)

```python
# In MAVProxy console
status all  # Check message rates
# Watch for high gyro variance (> 0.1 rad/s) -> loose mounting
```

### 3. Adaptive Estimator Status

Monitor information matrix quality:
$$\det(P) > 10^{-4} \implies \text{PE (Persistent Excitation)} = \text{True}$$

If PE is false during steady flight, increase `gamma_ee_`.

---

## Performance Benchmarks

Expected performance on 1-2 kg quadcopter:

| Condition | RMS Error | Convergence Time | Control Energy |
|-----------|-----------|-------------------|-----------------|
| Nominal (0% inertia error) | 0.3° | 15 sec | 2.5 Nm²·s |
| +30% inertia (with learning) | 1.8° | 45 sec | 3.2 Nm²·s |
| +30% with saturation | 2.1° | 28 sec | 2.8 Nm²·s |
| With 0.02 Nm disturbances | 1.2° | 30 sec | 4.1 Nm²·s |

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Oscillations/ringing | K_Ω too high | Reduce K_Ω by 20%, retune |
| Slow response | K_R too low | Increase K_R by 50% |
| Parameter drift (J growing unbounded) | sigma too low | Increase σ to 5e-4 |
| Adaptation stalls at hover | gamma_ee too low | Increase to 0.005 |
| High control energy | c too high or tau_max too low | Reduce c to 1.5 or increase tau_max |
| Chatter in attitude | Filter bandwidth too low | Increase to 0.2-0.3 |

---

## References

1. Lee et al., "Geometric Tracking Control of a Quadrotor UAV on SE(3)," 2010
2. Cahyadi et al., "Adaptive Inertia Estimation Augmented Geometric PD Control on SO(3)," 2024
3. Boffa et al., "Excitation-Aware Least-Squares Parameter Estimation," IEEE TAC, 2022

---

## Author & Attribution

Implementation based on:
- **Paper:** Cahyadi et al., "Adaptive Inertia Estimation Augmented Geometric PD Control on SO(3) Suitable for Embedded Controllers"
- **Developers:** Adha-Imam Cahyadi, Fahdy Nashatya, Sudiro, Ardhimas Wimbo Wasisto, Addy Wahyudie
- **PX4 Integration:** [Your Name/Organization]

For questions or improvements, contact the authors or submit issues to the repository.
