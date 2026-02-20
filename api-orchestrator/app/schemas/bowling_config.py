from datetime import datetime

from pydantic import BaseModel, Field


class SimulationMetadata(BaseModel):
    """Metadata about the simulation run."""

    scenario_id: str = Field(..., description="Unique identifier for the simulation scenario")
    timestamp: datetime = Field(..., description="ISO 8601 timestamp of simulation execution")
    operator: str = Field(..., description="Name or identifier of the simulation engine operator")
    version: str = Field(..., description="Version of the simulation engine")


class BallParameters(BaseModel):
    """Ball physical properties and release characteristics."""

    mass_kg: float = Field(
        ...,
        ge=1.0,
        le=10.0,
        description="Ball weight in kilograms (typically 6.8 kg ≈ 15 lbs)",
    )
    radius_m: float = Field(
        ..., ge=0.1, le=0.15, description="Ball radius in meters (typical: 0.1085m)"
    )
    initial_velocity_ms: float = Field(
        ...,
        ge=7.0,
        le=10.0,
        description="Ball speed at release in m/s (typical range: 7.5–9.0 m/s)",
    )
    rotational_speed_rpm: int = Field(
        ...,
        ge=0,
        le=600,
        description="Ball rotation rate in RPM (typical range: 200–400)",
    )
    launch_angle_deg: float = Field(
        ...,
        ge=0.0,
        le=3.0,
        description="Initial trajectory angle in degrees (0–3°)",
    )
    axis_tilt_deg: float = Field(
        ..., ge=0.0, le=90.0, description="Tilt angle of rotation axis in degrees (currently unused in sim.py)"
    )


class LaneConditions(BaseModel):
    """Lane surface and environmental properties."""

    friction_coefficient: float = Field(
        ...,
        ge=0.035,
        le=0.055,
        description="Surface friction (0.035–0.055). Lower=oily (less hook), Higher=dry (more hook)",
    )
    oil_pattern: str = Field(
        ..., description="Lane pattern name or type (informational, e.g., 'house') - currently unused in sim.py"
    )
    oil_distance_m: float = Field(
        ..., ge=10.0, le=15.0, description="Length of oil pattern in meters (typically 11.89m)"
    )
    lane_length_m: float = Field(
        ..., ge=17.0, le=20.0, description="Total lane length in meters (regulation: 18.29m)"
    )
    lane_width_m: float = Field(
        ...,
        ge=1.0,
        le=1.2,
        description="Lane width in meters (regulation: 1.067m)",
    )


class ReleasePoint(BaseModel):
    """Ball release position and targeting parameters."""

    lateral_offset_m: float = Field(
        ...,
        ge=-0.2,
        le=0.2,
        description="Starting position left/right of center in meters (-0.2 to 0.2m)",
    )
    target_board: int = Field(..., ge=1, le=39, description="Intended target board number (currently unused in sim.py)")
    breakpoint_board: int = Field(
        ..., ge=1, le=39, description="Hook breakpoint board number (currently unused in sim.py)"
    )


class PinSetup(BaseModel):
    """Pin configuration and collision properties."""

    pin_mass_kg: float = Field(..., ge=1.0, le=2.0, description="Pin weight in kilograms")
    pin_height_m: float = Field(
        ...,
        ge=0.3,
        le=0.45,
        description="Pin height in meters (regulation: 0.381m) - currently unused in sim.py (uses hardcoded pin positions)",
    )
    pin_spacing_m: float = Field(
        ...,
        ge=0.25,
        le=0.35,
        description="Distance between pin centers in meters (regulation: 0.305m) - currently unused in sim.py (uses hardcoded pin positions)",
    )
    coefficient_restitution: float = Field(
        ...,
        ge=0.5,
        le=1.0,
        description="Collision elasticity between ball and pins (0.72 typical)",
    )


class SimulationSettings(BaseModel):
    """Simulation execution parameters and behavior flags."""

    time_step_s: float = Field(
        ...,
        gt=0.0,
        le=0.01,
        description="Simulation timestep in seconds (0.001s = 1ms typical)",
    )
    max_duration_s: float = Field(
        ..., gt=0.0, description="Maximum simulation duration in seconds (typical: 5.0)"
    )
    enable_chain_reaction: bool = Field(
        ..., description="Enable probabilistic pin-to-pin knockdown propagation"
    )
    enable_deflection: bool = Field(
        ..., description="Enable ball deflection on pin collision (currently unused in sim.py)"
    )
    random_seed: int = Field(
        ..., ge=0, description="Random seed for reproducible stochastic behavior"
    )


class BowlingConfig(BaseModel):
    """Complete bowling simulation configuration with all parameters."""

    simulation_metadata: SimulationMetadata = Field(
        ..., description="Simulation execution metadata"
    )
    ball_parameters: BallParameters = Field(..., description="Ball physical properties")
    lane_conditions: LaneConditions = Field(..., description="Lane surface properties")
    release_point: ReleasePoint = Field(..., description="Ball release position")
    pin_setup: PinSetup = Field(..., description="Pin configuration")
    simulation_settings: SimulationSettings = Field(
        ..., description="Simulation execution parameters"
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "simulation_metadata": {
                    "scenario_id": "strike-attempt-001",
                    "timestamp": "2026-01-21T14:30:00Z",
                    "operator": "simulation-engine",
                    "version": "1.0.0",
                },
                "ball_parameters": {
                    "mass_kg": 6.8,
                    "radius_m": 0.1085,
                    "initial_velocity_ms": 8.5,
                    "rotational_speed_rpm": 320,
                    "launch_angle_deg": 0.3,
                    "axis_tilt_deg": 10,
                },
                "lane_conditions": {
                    "friction_coefficient": 0.044,
                    "oil_pattern": "house",
                    "oil_distance_m": 11.89,
                    "lane_length_m": 18.29,
                    "lane_width_m": 1.067,
                },
                "release_point": {
                    "lateral_offset_m": 0.0,
                    "target_board": 10,
                    "breakpoint_board": 7,
                },
                "pin_setup": {
                    "pin_mass_kg": 1.58,
                    "pin_height_m": 0.381,
                    "pin_spacing_m": 0.305,
                    "coefficient_restitution": 0.72,
                },
                "simulation_settings": {
                    "time_step_s": 0.001,
                    "max_duration_s": 5.0,
                    "enable_chain_reaction": True,
                    "enable_deflection": True,
                    "random_seed": 42,
                },
            }
        }
  