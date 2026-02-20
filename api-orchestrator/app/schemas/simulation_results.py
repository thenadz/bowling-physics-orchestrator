from typing import List, Optional

from pydantic import BaseModel, Field

from .simulation import SimulationMetadata


class SimulationExecutionMetadata(SimulationMetadata):
    """Extended metadata including execution results."""

    execution_timestamp: str = Field(
        ..., description="ISO 8601 timestamp when simulation execution began"
    )
    execution_duration_ms: float = Field(
        ..., ge=0.0, description="Total execution time in milliseconds"
    )
    status: str = Field(
        ..., description="Execution status ('completed', 'failed', etc.)"
    )


class InputParameters(BaseModel):
    """Parameters that were actually used in the simulation execution."""

    ball_velocity_ms: float = Field(
        ..., ge=7.0, le=10.0, description="Ball speed used (m/s)"
    )
    rotational_speed_rpm: int = Field(
        ..., ge=0, le=600, description="Ball rotation rate used (RPM)"
    )
    ball_mass_kg: float = Field(
        ..., ge=1.0, le=10.0, description="Ball mass used (kg)"
    )
    friction_coefficient: float = Field(
        ..., ge=0.035, le=0.055, description="Lane friction coefficient used"
    )
    launch_angle_deg: float = Field(
        ..., ge=0.0, le=3.0, description="Launch angle used (degrees)"
    )


class PinState(BaseModel):
    """State of an individual pin after simulation."""

    pin_number: int = Field(..., ge=1, le=10, description="Pin number (1-10)")
    knocked: bool = Field(..., description="Whether pin was knocked down")
    impact_velocity_ms: Optional[float] = Field(
        None,
        ge=0.0,
        description="Velocity of pin after impact in m/s (None if not struck)",
    )


class SimulationResultsData(BaseModel):
    """Outcome of the simulation execution."""

    pins_knocked: int = Field(
        ..., ge=0, le=10, description="Number of pins knocked down"
    )
    pins_standing: int = Field(
        ..., ge=0, le=10, description="Number of pins still standing"
    )
    pin_states: List[PinState] = Field(
        ..., description="Detailed state of each pin (10 pins total)"
    )
    is_strike: bool = Field(..., description="Whether all 10 pins were knocked")
    is_spare_possible: bool = Field(
        ..., description="Whether 9+ pins were knocked (spare possible)"
    )
    score_value: str = Field(
        ..., description="Bowling score notation ('X', '-', or pin count)"
    )


class TrajectoryAnalysis(BaseModel):
    """Ball trajectory characteristics and impact metrics."""

    hook_potential_cm: float = Field(
        ..., ge=0.0, description="Lateral deflection potential in centimeters"
    )
    entry_angle_deg: float = Field(
        ..., description="Angle at which ball enters pin deck (degrees)"
    )
    impact_velocity_ms: float = Field(
        ..., ge=0.0, description="Ball velocity when striking pins (m/s)"
    )
    ball_deflection_cm: float = Field(
        ..., description="Total lateral deflection in centimeters"
    )
    trajectory_length_m: float = Field(
        ...,
        ge=17.0,
        le=20.0,
        description="Lane length traveled (meters, typically 18.29m)",
    )


class TelemetryPoint(BaseModel):
    """Single telemetry measurement from ball trajectory."""

    time_s: float = Field(..., ge=0.0, description="Time elapsed since release (seconds)")
    position_m: dict = Field(
        ...,
        description="Ball position {x, y} in meters (x=lateral, y=down-lane)",
    )
    velocity_ms: dict = Field(
        ...,
        description="Ball velocity {x, y} in m/s (x=lateral, y=down-lane)",
    )
    speed_ms: float = Field(..., ge=0.0, description="Total ball speed in m/s")
    rotation_rpm: float = Field(..., ge=0.0, description="Ball rotation rate in RPM")


class TelemetrySummary(BaseModel):
    """Metadata about collected telemetry data."""

    data_points: int = Field(..., ge=0, description="Number of telemetry samples collected")
    sample_rate_hz: float = Field(
        ..., gt=0.0, description="Sampling rate in Hz (typically 1000 Hz)"
    )
    duration_s: float = Field(
        ..., ge=0.0, description="Total duration of telemetry recording (seconds)"
    )


class ModelMetadata(BaseModel):
    """Physics model configuration and assumptions used."""

    physics_model: str = Field(
        ..., description="Physics model type (e.g., 'simplified_rigid_body')"
    )
    friction_model: str = Field(
        ..., description="Friction model type (e.g., 'coulomb')"
    )
    collision_model: str = Field(
        ..., description="Collision model type (e.g., 'inelastic_cascade')"
    )
    assumptions: List[str] = Field(
        ...,
        description="List of assumptions/limitations of the physics model",
    )


class BowlingSimulationResults(BaseModel):
    """Complete bowling simulation results with all outputs and telemetry."""

    simulation_metadata: SimulationExecutionMetadata = Field(
        ..., description="Execution metadata including timing and status"
    )
    input_parameters: InputParameters = Field(
        ..., description="Parameters actually used in simulation"
    )
    simulation_results: SimulationResultsData = Field(
        ..., description="Pin and strike outcome data"
    )
    trajectory_analysis: TrajectoryAnalysis = Field(
        ..., description="Ball trajectory characteristics"
    )
    telemetry_summary: TelemetrySummary = Field(
        ..., description="Metadata about telemetry collection"
    )
    telemetry: List[TelemetryPoint] = Field(
        ..., description="Full trajectory telemetry array (~2,250 points at 1000 Hz)"
    )
    model_metadata: ModelMetadata = Field(
        ..., description="Physics model configuration and assumptions"
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
                    "execution_timestamp": "2026-01-22T04:01:14.827640+00:00Z",
                    "execution_duration_ms": 57.08,
                    "status": "completed",
                },
                "input_parameters": {
                    "ball_velocity_ms": 8.5,
                    "rotational_speed_rpm": 320,
                    "ball_mass_kg": 6.8,
                    "friction_coefficient": 0.044,
                    "launch_angle_deg": 0.3,
                },
                "simulation_results": {
                    "pins_knocked": 9,
                    "pins_standing": 1,
                    "pin_states": [
                        {
                            "pin_number": 1,
                            "knocked": True,
                            "impact_velocity_ms": 14.78,
                        }
                    ],
                    "is_strike": False,
                    "is_spare_possible": True,
                    "score_value": "9",
                },
                "trajectory_analysis": {
                    "hook_potential_cm": 69.6,
                    "entry_angle_deg": 0.85,
                    "impact_velocity_ms": 7.49,
                    "ball_deflection_cm": 12.6,
                    "trajectory_length_m": 18.29,
                },
                "telemetry_summary": {
                    "data_points": 2250,
                    "sample_rate_hz": 1000.0,
                    "duration_s": 2.25,
                },
                "telemetry": [
                    {
                        "time_s": 0.001,
                        "position_m": {"x": 0.0, "y": 0.0085},
                        "velocity_ms": {"x": 0.0, "y": 8.5},
                        "speed_ms": 8.5,
                        "rotation_rpm": 320,
                    }
                ],
                "model_metadata": {
                    "physics_model": "simplified_rigid_body",
                    "friction_model": "coulomb",
                    "collision_model": "inelastic_cascade",
                    "assumptions": [
                        "Uniform lane surface",
                        "Rigid ball and pins",
                        "No spin decay during flight",
                        "Simplified pin-pin interactions",
                    ],
                },
            }
        }
