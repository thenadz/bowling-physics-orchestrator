#!/usr/bin/env python3
"""
APQX Digital Thread - Bowling Simulation Engine
================================================
Simulates bowling ball physics with variable parameters to predict pin knockdown.

This simulation demonstrates digital thread integration:
- Design parameters (ball specs, lane conditions)
- Simulation execution (physics model)
- Telemetry generation (trajectory, impact data)
- Analytics (pin fall prediction)

Physics Model:
- Ball motion with friction and hook potential
- Pin collision dynamics with chain reaction
- Deflection and carry-down effects
"""

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
from scipy.spatial.distance import cdist


class BowlingSimulation:
    """
    Physics-based bowling simulation with configurable parameters.
    
    Implements simplified but realistic bowling mechanics including:
    - Ball trajectory with friction deceleration
    - Hook curve from rotational energy
    - Pin collision detection and cascade
    - Energy transfer and deflection
    """
    
    # Standard pin positions in meters (relative to head pin at origin)
    PIN_POSITIONS = np.array([
        [0.000, 0.000],      # Pin 1 (head pin)
        [-0.153, 0.216],     # Pin 2
        [0.153, 0.216],      # Pin 3
        [-0.305, 0.432],     # Pin 4
        [0.000, 0.432],      # Pin 5
        [0.305, 0.432],      # Pin 6
        [-0.458, 0.648],     # Pin 7
        [-0.153, 0.648],     # Pin 8
        [0.153, 0.648],      # Pin 9
        [0.458, 0.648],      # Pin 10
    ])
    
    def __init__(self, config_path: Path):
        """Load configuration and initialize simulation state."""
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.ball_params = self.config['ball_parameters']
        self.lane_params = self.config['lane_conditions']
        self.release = self.config['release_point']
        self.pin_params = self.config['pin_setup']
        self.sim_settings = self.config['simulation_settings']
        
        # Set random seed for reproducibility
        np.random.seed(self.sim_settings['random_seed'])
        
        # Initialize state
        self.pins_standing = np.ones(10, dtype=bool)
        self.trajectory = []
        self.telemetry = []
        self.impacts = []
        
    def run(self) -> Dict:
        """Execute the bowling simulation and return results."""
        start_time = datetime.now(timezone.utc)
        
        # Phase 1: Ball trajectory
        print("Simulating ball trajectory...")
        final_position, final_velocity, impact_angle = self._simulate_trajectory()
        
        # Phase 2: Impact and pin physics
        print("Calculating pin impacts...")
        self._simulate_pin_impacts(final_position, final_velocity, impact_angle)
        
        # Phase 3: Chain reaction
        if self.sim_settings['enable_chain_reaction']:
            print("Processing pin cascade...")
            self._simulate_pin_cascade()
        
        # Calculate results
        pins_knocked = int(np.sum(~self.pins_standing))
        
        end_time = datetime.now(timezone.utc)
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        results = {
            "simulation_metadata": {
                **self.config['simulation_metadata'],
                "execution_timestamp": start_time.isoformat() + "Z",
                "execution_duration_ms": round(duration_ms, 2),
                "status": "completed"
            },
            "input_parameters": {
                "ball_velocity_ms": self.ball_params['initial_velocity_ms'],
                "rotational_speed_rpm": self.ball_params['rotational_speed_rpm'],
                "ball_mass_kg": self.ball_params['mass_kg'],
                "friction_coefficient": self.lane_params['friction_coefficient'],
                "launch_angle_deg": self.ball_params['launch_angle_deg']
            },
            "simulation_results": {
                "pins_knocked": pins_knocked,
                "pins_standing": 10 - pins_knocked,
                "pin_states": [
                    {
                        "pin_number": i + 1,
                        "knocked": not self.pins_standing[i],
                        "impact_velocity_ms": self.impacts[i] if i < len(self.impacts) else None
                    }
                    for i in range(10)
                ],
                "is_strike": pins_knocked == 10,
                "is_spare_possible": pins_knocked >= 9,
                "score_value": self._calculate_score(pins_knocked)
            },
            "trajectory_analysis": {
                "hook_potential_cm": self._calculate_hook(),
                "entry_angle_deg": round(impact_angle, 2),
                "impact_velocity_ms": round(np.linalg.norm(final_velocity), 2),
                "ball_deflection_cm": round(final_position[0] * 100, 1),
                "trajectory_length_m": round(self.lane_params['lane_length_m'], 2)
            },
            "telemetry_summary": {
                "data_points": len(self.telemetry),
                "sample_rate_hz": 1.0 / self.sim_settings['time_step_s'],
                "duration_s": len(self.telemetry) * self.sim_settings['time_step_s']
            },
            "telemetry": self.telemetry,
            "model_metadata": {
                "physics_model": "simplified_rigid_body",
                "friction_model": "coulomb",
                "collision_model": "inelastic_cascade",
                "assumptions": [
                    "Uniform lane surface",
                    "Rigid ball and pins",
                    "No spin decay during flight",
                    "Simplified pin-pin interactions"
                ]
            }
        }
        
        return results
    
    def _simulate_trajectory(self) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Simulate ball trajectory from release to pin deck.
        
        Returns:
            (final_position, final_velocity, impact_angle)
        """
        # Initial conditions
        v0 = self.ball_params['initial_velocity_ms']
        angle_rad = math.radians(self.ball_params['launch_angle_deg'])
        lateral_offset = self.release['lateral_offset_m']
        
        # Convert board positions to meters (1 board ≈ 2.54 cm)
        board_to_m = 0.0254
        target_offset = (self.release['target_board'] - 20) * board_to_m
        
        # Position and velocity vectors
        position = np.array([lateral_offset, 0.0])  # [x, y]
        velocity = np.array([
            v0 * math.sin(angle_rad),
            v0 * math.cos(angle_rad)
        ])
        
        # Rotational parameters
        omega = self.ball_params['rotational_speed_rpm'] * 2 * math.pi / 60  # rad/s
        r = self.ball_params['radius_m']
        
        # Physics constants
        mu = self.lane_params['friction_coefficient']
        g = 9.81  # m/s²
        m = self.ball_params['mass_kg']
        dt = self.sim_settings['time_step_s']
        lane_length = self.lane_params['lane_length_m']
        oil_distance = self.lane_params['oil_distance_m']
        
        time = 0.0
        
        while position[1] < lane_length and time < self.sim_settings['max_duration_s']:
            # Record telemetry
            self.telemetry.append({
                'time_s': round(time, 4),
                'position_m': {
                    'x': round(position[0], 4),
                    'y': round(position[1], 4)
                },
                'velocity_ms': {
                    'x': round(velocity[0], 4),
                    'y': round(velocity[1], 4)
                },
                'speed_ms': round(np.linalg.norm(velocity), 3),
                'rotation_rpm': round(self.ball_params['rotational_speed_rpm'], 1)
            })
            
            # Calculate friction force (increases after oil pattern)
            if position[1] > oil_distance:
                effective_mu = mu * 1.8  # Higher friction on dry backend
            else:
                effective_mu = mu * 0.6  # Lower friction on oil
            
            friction_mag = effective_mu * m * g
            
            # Hook potential from rotation (simplified Magnus effect)
            if position[1] > oil_distance and omega > 0:
                hook_force_x = 0.025 * omega * r * m  # Reduced hook coefficient
            else:
                hook_force_x = 0.0
            
            # Update velocity (friction opposes motion, hook adds lateral)
            speed = np.linalg.norm(velocity)
            if speed > 0.1:
                friction_accel = -(friction_mag / m) * (velocity / speed)
                hook_accel = np.array([hook_force_x / m, 0.0])
                
                velocity += (friction_accel + hook_accel) * dt
            
            # Update position
            position += velocity * dt
            time += dt
            
            # Keep ball on lane (simplified boundary)
            position[0] = np.clip(position[0], -self.lane_params['lane_width_m']/2, 
                                 self.lane_params['lane_width_m']/2)
        
        # Calculate impact angle
        impact_angle = math.degrees(math.atan2(velocity[0], velocity[1]))
        
        return position, velocity, impact_angle
    
    def _simulate_pin_impacts(self, ball_pos: np.ndarray, ball_vel: np.ndarray, 
                              impact_angle: float):
        """
        Calculate which pins are directly struck by the ball.
        """
        ball_x = ball_pos[0]
        
        # Ball radius and pin radius
        ball_r = self.ball_params['radius_m']
        pin_r = 0.06  # ~6cm pin diameter
        collision_distance = ball_r + pin_r
        
        # Check collision with each pin (pins are at y=0 in local coords)
        impact_velocity_mag = np.linalg.norm(ball_vel)
        
        # Use ball's final X position to check lateral alignment
        for i, pin_pos in enumerate(self.PIN_POSITIONS):
            # Calculate distance from ball center to pin center (2D)
            dx = ball_x - pin_pos[0]
            dy = 0.0 - pin_pos[1]  # Ball is entering pin deck at y=0
            distance = math.sqrt(dx**2 + dy**2)
            
            # More generous collision detection for initial contact
            if distance < collision_distance * 1.5:  # 1.5x for glancing blows
                # Direct or glancing hit - pin knocked down
                self.pins_standing[i] = False
                
                # Calculate impact energy transfer (reduced for glancing)
                angle_factor = max(0.4, 1.0 - (distance / collision_distance - 1.0))
                impact_energy = 0.5 * self.ball_params['mass_kg'] * impact_velocity_mag**2
                transferred_energy = impact_energy * self.pin_params['coefficient_restitution'] * angle_factor
                
                # Estimate pin velocity after impact
                pin_velocity = math.sqrt(2 * transferred_energy / self.pin_params['pin_mass_kg'])
                self.impacts.append(round(pin_velocity, 2))
            else:
                self.impacts.append(None)
    
    def _simulate_pin_cascade(self):
        """
        Simulate secondary pin knockdowns from pin-to-pin collisions.
        """
        max_iterations = 5
        
        for iteration in range(max_iterations):
            knocked_this_round = []
            
            for i in range(10):
                if self.pins_standing[i] and self.impacts[i] is None:
                    # Check if any neighboring knocked pins could hit this one
                    for j in range(10):
                        if not self.pins_standing[j] and self.impacts[j] is not None:
                            distance = np.linalg.norm(self.PIN_POSITIONS[i] - self.PIN_POSITIONS[j])
                            
                            # If knocked pin is close and has sufficient energy
                            if distance < 0.5 and self.impacts[j] > 2.0:
                                # Probabilistic knock based on energy and distance
                                knock_probability = min(0.8, self.impacts[j] / 5.0) * (1 - distance / 0.5)
                                
                                if np.random.random() < knock_probability:
                                    knocked_this_round.append(i)
                                    break
            
            # Apply knockdowns
            for i in knocked_this_round:
                self.pins_standing[i] = False
                # Reduced energy for secondary impacts
                self.impacts[i] = max(1.0, (self.impacts[max(0, i-1)] or 2.0) * 0.6)
            
            if not knocked_this_round:
                break
    
    def _calculate_hook(self) -> float:
        """Calculate total hook potential in centimeters."""
        rpm = self.ball_params['rotational_speed_rpm']
        velocity = self.ball_params['initial_velocity_ms']
        friction = self.lane_params['friction_coefficient']
        
        # Simplified hook calculation
        hook_cm = (rpm / 100) * (friction / 0.05) * (7.0 / velocity) * 30
        return round(hook_cm, 1)
    
    def _calculate_score(self, pins_knocked: int) -> str:
        """Return bowling score notation."""
        if pins_knocked == 10:
            return "X (Strike)"
        elif pins_knocked == 0:
            return "- (Gutter)"
        else:
            return str(pins_knocked)


def main():
    """Main simulation entry point."""
    script_dir = Path(__file__).parent
    config_path = script_dir / "config.json"
    results_path = script_dir / "results.json"
    
    print("=" * 60)
    print("APQX Bowling Simulation Engine v1.0.0")
    print("Digital Thread Demonstration - Physics Model")
    print("=" * 60)
    print()
    
    if not config_path.exists():
        print(f"ERROR: Configuration file not found: {config_path}")
        sys.exit(1)
    
    try:
        # Initialize and run simulation
        sim = BowlingSimulation(config_path)
        results = sim.run()
        
        # Save results
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print()
        print("=" * 60)
        print("SIMULATION RESULTS")
        print("=" * 60)
        print(f"Pins Knocked: {results['simulation_results']['pins_knocked']} / 10")
        print(f"Strike: {results['simulation_results']['is_strike']}")
        print(f"Entry Angle: {results['trajectory_analysis']['entry_angle_deg']}°")
        print(f"Hook Potential: {results['trajectory_analysis']['hook_potential_cm']} cm")
        print(f"Impact Velocity: {results['trajectory_analysis']['impact_velocity_ms']} m/s")
        print(f"Execution Time: {results['simulation_metadata']['execution_duration_ms']} ms")
        print()
        print(f"Results saved to: {results_path}")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print(f"ERROR: Simulation failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
