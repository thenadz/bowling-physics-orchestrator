import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.bowling_config import CreateSimulationReq
from app.schemas.simulation_results import Coordinate, TelemetryPoint
from app.schemas.responses import CreateOrGetSimulationResp, GetSimulationResultsResp, SimulationResultsBody, GetTelemetryResp, HealthCheckResp
from app.schemas.health_check_state import HealthCheckState
from app.service.simulation_service import SimulationService
from app.api.deps import get_simulation_service

logger = logging.getLogger(__name__)

router = APIRouter()

# Requirement: Submit bowling config (velocity, RPM, friction, angle) and queue job
@router.post("/simulations")
async def create_simulation(
    request: CreateSimulationReq,
    service: SimulationService = Depends(get_simulation_service)
) -> CreateOrGetSimulationResp:
    """
    Endpoint to create & queue a new bowling simulation based on provided configuration.
    """
    logger.debug(f"API request to create simulation with velocity={request.velocity}, rpm={request.rpm}, friction={request.friction}, angle={request.angle}, lateral_offset={request.lateral_offset}")
    sim = service.create_simulation(
        velocity=request.velocity,
        rpm=request.rpm,
        friction=request.friction,
        launch_angle=request.angle,
        lateral_offset=request.lateral_offset)
    logger.debug(f"API created simulation {sim.id} with state {sim.status}")
    return CreateOrGetSimulationResp(simulation_id=sim.id, state=sim.status)

# Requirement: Query job state (pending/running/completed/failed) with metadata
@router.get("/simulations/{simulation_id}")
async def get_simulation(simulation_id: uuid.UUID, service: SimulationService = Depends(get_simulation_service)) -> CreateOrGetSimulationResp:
    """
    Endpoint to retrieve the state of a bowling simulation by its ID.
    Once `SimulationState.COMPLETED`, results can be retrieved via the /simulations/{simulation_id}/results endpoint.
    """
    logger.debug(f"API request to get simulation with ID: {simulation_id}")
    simulation = service.get_simulation(simulation_id)
    # handle sim ID not found
    if simulation is None:
        logger.warning(f"Simulation with ID: {simulation_id} not found.")
        raise HTTPException(status_code=404, detail=f"Simulation {simulation_id} not found")
        
    logger.debug(f"API retrieved simulation {simulation_id} with state {simulation.status}")
    return CreateOrGetSimulationResp(simulation_id=simulation_id, state=simulation.status)

# Requirement: Retrieve pins knocked, hook potential, impact velocity, execution time
@router.get("/simulations/{simulation_id}/results")
async def get_simulation_results(simulation_id: uuid.UUID, service: SimulationService = Depends(get_simulation_service)) -> GetSimulationResultsResp:
    """
    Endpoint to retrieve the results of a bowling simulation by its ID. Only call once the simulation has completed.
    """
    logger.debug(f"API request to get simulation results for ID: {simulation_id}")
    simulation = service.get_simulation(simulation_id)
    
    # handle sim ID not found or results not yet available or failed
    if simulation is None or simulation.results is None:
        logger.warning(f"Simulation results for ID: {simulation_id} not found.")
        raise HTTPException(status_code=404, detail=f"Simulation results for {simulation_id} not found")
    
    logger.debug(f"API retrieved simulation {simulation_id} with results: pins_knocked={simulation.results.pins_knocked}, hook_potential={simulation.results.hook_potential}, impact_velocity={simulation.results.impact_velocity}, execution_time={simulation.results.execution_duration}")
    results: SimulationResultsBody = SimulationResultsBody(
        pins_knocked=simulation.results.pins_knocked,
        hook_potential=simulation.results.hook_potential,
        impact_velocity=simulation.results.impact_velocity,
        execution_time=simulation.results.execution_duration
    )
    
    logger.debug(f"API retrieved simulation results for ID: {simulation_id}")
    return GetSimulationResultsResp(simulation_id=simulation_id, results=results)

# Requirement: Retrieve full trajectory data with downsampling options
@router.get("/telemetry/{simulation_id}")
async def get_telemetry(simulation_id: uuid.UUID, service: SimulationService = Depends(get_simulation_service)) -> GetTelemetryResp:
    """
    Endpoint to retrieve the telemetry data of a bowling simulation by its ID.
    Only call once the simulation has completed.
    """
    logger.debug(f"API request to get telemetry data for ID: {simulation_id}")
    simulation = service.get_simulation(simulation_id)
    
    # handle sim ID not found or telemetry not yet available or failed
    if simulation is None or simulation.telemetry is None:
        logger.warning(f"Telemetry data for ID: {simulation_id} not found.")
        raise HTTPException(status_code=404, detail=f"Telemetry data for {simulation_id} not found")
    
    logger.debug(f"API retrieved simulation {simulation_id} with telemetry data points: {len(simulation.telemetry)}")
    
    # TODO - add query params for downsampling options (e.g., sample_rate, time_window) and apply to telemetry data before returning
    telemetry = [TelemetryPoint(
        time_s=point.time,
        position_m=Coordinate(x=point.position_x, y=point.position_y),
        velocity_ms=Coordinate(x=point.velocity_x, y=point.velocity_y),
        speed_ms=point.speed,
        rotation_rpm=point.rotation
    ) for point in simulation.telemetry]
    
    logger.debug(f"API retrieved telemetry data for ID: {simulation_id}")
    return GetTelemetryResp(simulation_id=simulation_id, telemetry=telemetry)

# Requirement: service up (if we get here, we're alive)
@router.get("/health/live")
def health_live():
    """
    Endpoint to check the liveness of the application.
    Will always return alive if it responds.
    """
    logger.debug("API health check (live) endpoint called.")
    return HealthCheckResp(status=HealthCheckState.ALIVE)

# Requirement: dependencies available
@router.get("/health/ready")
async def health_ready():
    """
    Endpoint to check the readiness of the application.
    Will return ready if all critical dependencies are available (e.g., database, message queuing service).
    """
    status = HealthCheckState.READY # TODO - placeholder until actual dependency checks are implemented
    logger.debug(f"API health check (ready) endpoint called with status: {status}")
    # TODO: add checks for critical dependencies (e.g., database connectivity, message queue availability) and return appropriate status
    return HealthCheckResp(status=status)