# Pixhawk Motor & ESC Connection Guide

## 🔌 Motor Connection Overview

Your Pixhawk has **8 output channels** on the top:
- **MAIN OUT 1-4** - Primary motor outputs (quadcopter uses these)
- **AUX OUT 5-8** - Auxiliary outputs (not needed for basic quad)

## 📍 Pixhawk 2.4.8 Motor Pin Layout

```
Looking at Pixhawk from above:

┌─────────────────────────────────────┐
│   MAIN OUT CONNECTORS (Top Row)     │
│                                     │
│  [1]  [2]  [3]  [4]  [5]  [6]  ... │
│   ↓    ↓    ↓    ↓    ↓    ↓       │
│  FR   FL   RL   RR   AUX  AUX  ... │
│                                     │
└─────────────────────────────────────┘

Front of Pixhawk:
    FL (Motor 2)      FR (Motor 1)
          [2]              [1]
          
          
          [3]              [4]
    RL (Motor 3)      RR (Motor 4)
```

## 📋 Quadcopter Motor Wiring

### Motor Positions
| Motor | Position | Pin | Spin Direction | Notes |
|-------|----------|-----|-----------------|-------|
| 1 | Front-Right | MAIN OUT 1 | **Clockwise (CW)** | Looking from above |
| 2 | Front-Left | MAIN OUT 2 | **Counter-Clockwise (CCW)** | Looking from above |
| 3 | Rear-Left | MAIN OUT 3 | **Clockwise (CW)** | Looking from above |
| 4 | Rear-Right | MAIN OUT 4 | **Counter-Clockwise (CCW)** | Looking from above |

### Spin Pattern (Viewed from Above)
```
    2 ↺          1 ↻
   CCW            CW
    
    
    3 ↻          4 ↺
    CW            CCW
```

## 🔧 Connection Steps

### 1. ESC to Motor Connection
Each ESC (Electronic Speed Controller) has 3 wires to motor:
```
ESC ━━━━━ MOTOR
 ① ——— ① (Wire 1)
 ② ——— ② (Wire 2)
 ③ ——— ③ (Wire 3)

If motor spins wrong direction: SWAP ANY 2 WIRES
```

### 2. ESC to Pixhawk Connection
Each ESC needs a **3-pin connector** to Pixhawk:
```
ESC Cable ━━━━━ Pixhawk MAIN OUT
┌─────────┐
│ BLACK   │ ——— GND (black wire on Pixhawk pin)
│ RED     │ ——— 5V  (red wire on Pixhawk pin)
│ WHITE   │ ——— SIG (white/yellow wire on Pixhawk pin)
└─────────┘

ESC Pin 1 (Black) → MAIN OUT GND
ESC Pin 2 (Red)   → MAIN OUT 5V
ESC Pin 3 (White) → MAIN OUT SIG
```

### 3. Power Module Connection
The power module provides power to Pixhawk and distributes to ESCs:

```
Battery (XT60)
    ↓
Power Module (PM)
    ├─→ To Pixhawk (6-pin connector)
    ├─→ To ESC Distribution
    └─→ Ground distribution
```

**Power Module → Pixhawk:**
- Red wire: 5V power
- Black wire: GND
- Yellow wire: Voltage sense
- Black wire: Current sense
- These go into the 6-pin "POWER" connector on Pixhawk

## ✅ Verification Checklist

- [ ] **Motor 1 (FR)** connected to MAIN OUT 1
- [ ] **Motor 2 (FL)** connected to MAIN OUT 2
- [ ] **Motor 3 (RL)** connected to MAIN OUT 3
- [ ] **Motor 4 (RR)** connected to MAIN OUT 4
- [ ] **All ESC signal wires** (white/yellow) properly seated
- [ ] **All ESC power wires** (red/black) properly seated
- [ ] **Power module** connected to Pixhawk POWER connector
- [ ] **Battery** connected to power module (XT60)
- [ ] **No loose connectors** or exposed wires

## 🔄 If Motors Spin Wrong Direction

1. **In Phase 3 (motor test)**, note which motor spins backwards
2. On that ESC, **swap any 2 of the 3 motor wires**
3. Retest - it should now spin correct direction

Example:
```
If Motor 1 (should be CW) spins CCW:
  Current:  ESC [1-2-3] → Motor [1-2-3]
  Fix:      ESC [1-2-3] → Motor [2-1-3]  (swap wires 1 and 2)
```

## 🚨 Common Issues

### No Motor Response
1. ✓ Check all ESC signal wires seated in MAIN OUT pins
2. ✓ Check MAIN OUT connector isn't loose
3. ✓ Verify Pixhawk is getting power (green light)
4. ✓ Try moving each motor to MAIN OUT 1 to isolate problem

### Motors Spin Weakly
1. ✓ Check battery is fully charged
2. ✓ Check power module is providing voltage
3. ✓ Check ESC not damaged (test with battery directly)

### One Motor Doesn't Spin
1. ✓ Check ESC signal wire connection
2. ✓ Check ESC power connectors (red/black)
3. ✓ Try ESC on different MAIN OUT pin
4. ✓ Check ESC isn't in failsafe state

### Wrong Spin Direction
1. ✓ Swap 2 motor wires on that ESC
2. ✓ Retest

## 📸 Visual Connection Guide

```
Pixhawk Top View:
┌──────────────────────────────────────────┐
│           MAIN OUT PINS                  │
│  ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐      │
│  │1│ │2│ │3│ │4│ │5│ │6│ │7│ │8│      │
│  └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘      │
│   ↓   ↓   ↓   ↓   ↓   ↓   ↓   ↓        │
│  [ESC1][ESC2][ESC3][ESC4][AUX1][...]   │
│   ↓     ↓     ↓     ↓                    │
│  M1    M2    M3    M4                    │
│  FR    FL    RL    RR                    │
└──────────────────────────────────────────┘

Each ESC = 3-pin connector (GND, 5V, SIG)
```

## 🧪 Testing Process

### Phase 2: Benchtop (Props OFF)
- ESCs get power from Pixhawk
- Test each motor individually
- Watch for spin direction

### Phase 3: Hover (Props ON)
- Full system test with liftoff
- All motors spin together
- Verify control response

## 📞 Troubleshooting Quick Reference

| Problem | Check | Fix |
|---------|-------|-----|
| No motors spin | Signal wires | Reseat MAIN OUT connectors |
| One motor quiet | Battery/PM voltage | Check power module connection |
| Wrong spin direction | ESC wires | Swap 2 motor wires on that ESC |
| Unstable hover | Motor response | Verify all motors responding equally |

---

## Key Takeaway

For your **Pixhawk 2.4.8 quad**:
- ✅ Motors **1-4** → **MAIN OUT 1-4** (not AUX)
- ✅ Each needs **3-pin connector** (GND, 5V, SIG)
- ✅ Power comes from **Power Module**
- ✅ Signal control from **Pixhawk processor**

If motors don't respond in Phase 2:
1. First, verify battery voltage (multimeter check)
2. Check power module is providing 5V to Pixhawk
3. Check ESC signal wires are seated properly
4. Test individual ESCs by moving to MAIN OUT 1
