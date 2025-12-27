# AIC Controller - Quick Reference

## Fast Setup (5 minutes)

### 1. Measure/Estimate Inertia
```cpp
// Edit: src/modules/attitude_controller_aic/AttitudeControllerAIC.cpp
J_init(0, 0) = 0.040f;  // Ixx - replace with your value
J_init(1, 1) = 0.040f;  // Iyy
J_init(2, 2) = 0.025f;  // Izz
```

**Quick estimation:** Oscillate your quad by hand, measure period T
- $I = \frac{m L^2}{12} \approx 0.002 \times \text{(arm length in meters)}^2 \times \text{(motor mass in kg)}$

### 2. Set Control Gains (from tuning table)

| Gain | Conservative | Aggressive | Note |
|------|-------------|-----------|------|
| K_R | 3.5 | 7.0 | Attitude response speed |
| K_Ω | 0.21 | 0.5 | Damping (watch for oscillation) |
| K | 0.05 | 0.2 | Robust damping |

### 3. Enable and Arm
```bash
# In PX4
param set MC_ENABLE_AIC 1
arm
```

### 4. Test (Slow attitude command)
- Send 5° roll setpoint → should reach in <1 second with minimal overshoot
- If oscillates → decrease K_Ω by 30%
- If too sluggish → increase K_R by 50%

---

## Control Law (One-Liner)

$$\tau = -K_R e_R - K_\Omega e_\Omega + \underbrace{Y(\omega,\alpha) \hat{J}}_{\text{learns inertia}} - K s + \text{saturation}$$

**Human readable:**
1. **Push attitude error to zero** with PD feedback (-K_R e_R - K_Ω e_Ω)
2. **Learn and compensate dynamics** with adaptive feedforward (Y·θ̂)
3. **Smooth out disturbances** with robust term (-K·s)
4. **Clip motor commands** to physical limits

---

## Adaptation Modes

### Mode A: **Learning Mode** (startup, payload changes)
**When:** Information quality determinant(P) < 0.001
**What:** Actively increases learning rate
**Goal:** Quickly adapt to new inertia

**Settings:**
```cpp
gamma = 2.0f;      // Fast learning
sigma = 5e-5f;     // Minimal drift
gamma_ee = 0.005f; // Strong excitation
```

### Mode B: **Tracking Mode** (normal flight)
**When:** determinant(P) > 0.001 (persistent excitation detected)
**What:** Reduces learning rate to prevent noise-induced drift
**Goal:** Stable tracking with minimal parameter drift

**Settings:**
```cpp
gamma = 1.5f;      // Moderate
sigma = 1e-4f;     // Standard
gamma_ee = 0.001f; // Gentle
```

### Mode C: **Conservative Mode** (high noise, disturbances)
**When:** Manual override or detected instability
**What:** Disables adaptation, uses fixed inertia estimate
**Goal:** Safety - prevent learning from corrupted data

**Settings:**
```cpp
gamma = 0.1f;      // Nearly off
sigma = 1e-3f;     // Strong leakage
gamma_ee = 0.0f;   // Disabled
```

---

## Key Equations (Implementation Checklist)

- [ ] **Attitude error (SO(3)):** $e_R = \frac{1}{2} \text{vee}(R_d^T R - R^T R_d)$
- [ ] **Angular velocity error:** $e_\Omega = \Omega - R^T R_d \Omega_d$
- [ ] **Composite error:** $s = e_\Omega + 2 e_R$ (c = 2)
- [ ] **Regressor matrix:** $\tau_{rb} = Y(\omega, \alpha) \theta$ where θ = [Jxx, Jyy, Jzz, ...]
- [ ] **IWG update:** $\Delta\theta = -\Gamma (I + \lambda P)^{-1} Y^T s - \sigma \Gamma \theta$
- [ ] **Info accumulation:** $P_{k+1} = P_k + \Delta t \cdot Y_k^T Y_k$
- [ ] **SPD projection:** clip eigenvalues to [J_min, J_max]
- [ ] **Final torque:** $\tau = -K_R e_R - K_\Omega e_\Omega + Y \hat{\theta} - K s$

---

## Performance Indicators

### Good Tracking
- **Attitude error:** < 2° RMS in steady-state
- **Overshoot:** < 10% on attitude step commands
- **Settling time:** < 2 seconds
- **Parameter drift:** < 5% over 10 minutes

### Adaptive Learning
- **Convergence time:** < 60 seconds to reach inertia within ±10% of true value
- **Information growth:** det(P) increasing over time
- **Torque smoothness:** No jitter or oscillation in τ commands

### System Health
- **Gyro variance:** < 0.05 rad/s (indicates good sensor quality)
- **Actuator saturation:** < 5% of mission time (else increase tau_max)
- **Control energy:** < 5 Nm²·s for 10-second maneuver

---

## Emergency Fallback

If learning becomes unstable:

**Option 1: Disable adaptation immediately**
```cpp
gamma = 0.0f;  // Freeze all learning
```

**Option 2: Reset to initial estimate**
```cpp
controller.reset(J_initial);  // Restart learning from scratch
```

**Option 3: Switch to PD-only control**
```cpp
// Set feedback gains only, ignore adaptive terms
K_R = 8.0f;  (increase to compensate)
K_Omega = 0.5f;
// Inertia terms become zero
```

---

## File Locations

| Task | File | Line(s) |
|------|------|---------|
| Change inertia estimate | AttitudeControllerAIC.cpp | ~65 |
| Tune control gains | AttitudeControllerAIC.cpp | ~70 |
| Adjust adaptation speed | AttitudeControllerAIC.cpp | ~77 |
| Set actuator limits | AttitudeControllerAIC.cpp | ~79 |
| Filter bandwidth | AttitudeControllerAIC.cpp | ~81 |

---

## Typical Flight Profile

```
Time:     0      10s      30s      40s      60s
State:   [INIT] [LEARN]  [TRACK]  [PAYLOAD] [LEARN->TRACK]
           │      │        │        │         │
         Arm   Maneuver  Steady   Drop     Re-adapt
           
Ihat:   J0→    →J0+Δ     Stable   J0       →J0 again
        
det(P): 0  ↗     stable   stable   ↗        stable
```

---

## Common Commands (MAVProxy)

```bash
# Check parameters
param show MC_AIC_*

# Update inertia estimate
param set MC_AIC_J_XX 0.045

# Adjust learning rate
param set MC_AIC_GAMMA 2.0

# Monitor determinant(P)
watch attitude  # Watch e_R, e_Omega for convergence

# Log data
log save /tmp/test.bin
```

---

## Citation

If using this controller in research, cite:

```bibtex
@article{cahyadi2024adaptive,
  title={Adaptive Inertia Estimation Augmented Geometric PD Control on SO(3) 
         Suitable for Embedded Controllers},
  author={Cahyadi, Adha Imam and Nashatya, Fahdy and Sudiro and Wimbo, Ardhimas and Wahyudie, Addy},
  journal={International Journal of Dynamics and Control},
  year={2024}
}
```

---

**Ready to fly!** ✈️
