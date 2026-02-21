import uuid
from typing import List

from pydantic import BaseModel, Field

from .simulation_state import SimulationState
from .health_check_state import HealthCheckState
from .simulation_results import TelemetryPoint

class CreateOrGetSimulationResp(BaseModel):
    simulation_id: uuid.UUID = Field(..., description="Unique identifier for the simulation")
    state: SimulationState = Field(..., description="Current state of the simulation")

class SimulationResultsBody(BaseModel):
    pins_knocked: int = Field(
        ..., ge=0, le=10, description="Number of pins knocked down"
    )
    hook_potential: float = Field(
        ..., ge=0.0, description="Calculated hook potential based on ball and lane conditions"
    )
    impact_velocity: float = Field(
        ..., ge=0.0, description="Ball velocity at the moment of impact with the pins"
    )
    execution_time: float = Field(
        ..., ge=0.0, description="Total execution time of the simulation in milliseconds"
    )

class GetSimulationResultsResp(BaseModel):
    simulation_id: uuid.UUID = Field(..., description="Unique identifier for the simulation")
    results: SimulationResultsBody = Field(..., description="Simulation results data")

class GetTelemetryResp(BaseModel):
    simulation_id: uuid.UUID = Field(..., description="Unique identifier for the simulation")
    telemetry: List[TelemetryPoint] = Field(..., description="Detailed telemetry data from the simulation execution")

class HealthCheckResp(BaseModel):
    status: HealthCheckState = Field(..., description="Health status of the application (e.g., 'alive', 'ready')")