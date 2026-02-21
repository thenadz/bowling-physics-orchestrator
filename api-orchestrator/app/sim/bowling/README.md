# 🎳 Bowling Physics Simulation Engine

**APQX Digital Thread Demonstration**

A physics-based bowling simulator that models ball trajectory, pin collisions, and chain reactions. This simulation demonstrates digital thread principles: configurable parameters yield variable outcomes with rich telemetry.

## Quick Start

```bash
# Install dependencies
pip install numpy scipy pydantic

# Run simulation with default parameters
python sim.py

# Output: results.json with 2,250+ telemetry points
```

## Input Configuration (`config.json`)

The simulation accepts a JSON configuration file with the following parameters:

### Ball Parameters
- **`initial_velocity_ms`**: Ball speed at release (7.5–9.0 m/s typical)
- **`rotational_speed_rpm`**: Ball rotation rate (200–400 RPM)
- **`mass_kg`**: Ball weight (6.8 kg ≈ 15 lbs)
- **`launch_angle_deg`**: Initial trajectory angle (0–3°)

### Lane Conditions
- **`friction_coefficient`**: Surface friction (0.035–0.055)
  - Lower = oily lane (less hook)
  - Higher = dry lane (more hook)
- **`oil_pattern`**: Lane pattern name (informational)
- **`oil_distance_m`**: Length of oil pattern (typically 11.89m)

### Release Point
- **`lateral_offset_m`**: Starting position left/right of center (-0.2 to 0.2m)
- **`target_board`**: Intended target board number
- **`breakpoint_board`**: Hook breakpoint board

## Output Data (`results.json`)

### Simulation Results
```json
{
  "simulation_results": {
    "pins_knocked": 9,
    "pins_standing": 1,
    "is_strike": false,
    "pin_states": [
      {
        "pin_number": 1,
        "knocked": true,
        "impact_velocity_ms": 14.78
      },
      ...
    ]
  }
}
```

### Trajectory Analysis
```json
{
  "trajectory_analysis": {
    "hook_potential_cm": 69.6,
    "entry_angle_deg": 0.85,
    "impact_velocity_ms": 7.49,
    "ball_deflection_cm": 12.6
  }
}
```

### Telemetry Array (2,250+ points)

Each telemetry point contains:
```json
{
  "time_s": 1.125,
  "position_m": {
    "x": 0.0492,
    "y": 9.3983
  },
  "velocity_ms": {
    "x": 0.043,
    "y": 8.2085
  },
  "speed_ms": 8.209,
  "rotation_rpm": 320
}
```

**Telemetry Statistics:**
- **Data points**: ~2,250 per simulation run
- **Sample rate**: 1,000 Hz (1ms timestep)
- **Duration**: ~2.5 seconds of ball flight
- **File size**: ~320 KB per simulation

## Parameter Impact Examples

### Strike Configuration (Target: 10/10 pins)
```json
{
  "initial_velocity_ms": 8.5,
  "rotational_speed_rpm": 320,
  "friction_coefficient": 0.044,
  "launch_angle_deg": 0.3,
  "lateral_offset_m": 0.0
}
```
**Expected Result**: 9-10 pins knocked, hook potential 65-70cm

### High Hook Configuration
```json
{
  "initial_velocity_ms": 8.0,
  "rotational_speed_rpm": 400,
  "friction_coefficient": 0.050,
  "launch_angle_deg": 0.5,
  "lateral_offset_m": 0.15
}
```
**Expected Result**: Variable pins (6-9), hook potential 85-100cm

### Straight Ball Configuration
```json
{
  "initial_velocity_ms": 8.8,
  "rotational_speed_rpm": 150,
  "friction_coefficient": 0.038,
  "launch_angle_deg": 0.2,
  "lateral_offset_m": 0.0
}
```
**Expected Result**: 7-9 pins, hook potential 30-40cm

## Physics Model

### Ball Trajectory
- **Friction model**: Coulomb friction with oil/dry zones
  - Oil zone: 60% friction coefficient
  - Dry zone: 180% friction coefficient (backend hook)
- **Hook mechanics**: Simplified Magnus effect from rotation
- **Boundary conditions**: Ball constrained to lane width

### Pin Collision
- **Detection**: Euclidean distance threshold (ball radius + pin radius × 1.5)
- **Energy transfer**: Inelastic collision with coefficient of restitution
- **Cascade model**: Probabilistic pin-to-pin knockdown propagation

### Assumptions & Limitations
- Uniform lane surface (no board variations)
- Rigid ball and pins (no deformation)
- No spin decay during flight
- Simplified pin-pin interaction model
- Deterministic physics (no random variation)

## Use Cases for Backend Platform

### 1. Parameter Sweep Analysis
Run simulations with varying velocity/RPM combinations to find correlations:
```python
for velocity in [7.5, 8.0, 8.5, 9.0]:
    for rpm in [200, 250, 300, 350, 400]:
        # Submit simulation job with these parameters
        # Collect and analyze results
```

### 2. Telemetry Storage
Store 2,250+ trajectory points per simulation:
- Time-series database (InfluxDB/TimescaleDB)
- Document store (MongoDB) with spatial indexing
- Relational DB with JSON columns

### 3. Analytics Queries
- Average pins knocked by velocity range
- Hook correlation with RPM
- Friction impact on carry percentage
- Entry angle vs. strike rate

### 4. Digital Thread Demonstration
Shows complete traceability:
- **Design Parameters**: Input config (velocity, RPM, friction)
- **Simulation Execution**: Physics model run
- **Telemetry Generation**: 2,250+ data points
- **Analytics**: Pin fall prediction, performance metrics

## File Structure

```
bowling/
├── sim.py              # Main simulation engine (~380 lines)
├── config.json         # Input parameters
├── results.json        # Output with full telemetry (~320 KB)
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Dependencies

- **numpy** (≥1.24.0): Vector math, trajectory calculations
- **scipy** (≥1.10.0): Spatial distance calculations
- **pydantic** (≥2.0.0): Configuration validation (future use)

## Performance

- **Execution time**: 25-60 ms per simulation
- **Memory usage**: ~10 MB peak
- **Output size**: ~320 KB JSON per run
- **Scalability**: Can run 1,000+ simulations per minute on single core

## Future Enhancements

- **Non-deterministic physics**: Add randomness for realistic variance
- **Advanced pin models**: Individual pin physics with tipping dynamics
- **Lane topology**: Model board-to-board friction variations
- **Ball spin decay**: More realistic hook trajectory over time
- **Streaming telemetry**: Emit data points during simulation instead of batch output

---

**Version**: 1.0.0  
**Last Updated**: January 2026  
**Contact**: APQX Digital Operations and Integration Team
