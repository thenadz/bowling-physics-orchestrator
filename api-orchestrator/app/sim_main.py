import logging
import uuid

from datetime import datetime
from typing import cast
from sqlalchemy.orm import Session

from app.config import settings
from app.core.logging import configure_logging
from app.db import models
from app.db.session import DbSession
from app.queue.session import RedisSession
from app.service.simulation_service import SimulationService
from app.sim.sim_harness import run_simulation

if __name__ == "__main__":
    configure_logging()
    logger = logging.getLogger("sim-worker")
    
    logger.info("Starting simulation worker...")
    
    redis = RedisSession
    
    # TODO - consider using a more robust worker framework like Celery or RQ for better performance and reliability in production environment
    while True:
        try:
            # block until a new simulation ID is available in the queue
            item: tuple[str, str] | None = cast(tuple[str, str] | None, redis.blpop([settings.queue_name], timeout=30)) # type: ignore
        
            if item is None:
                logger.info("Timed out after 30s waiting for queue. Trying again.")
                continue
        except Exception as e:
            logger.error(f"Error popping from the queue. Error: {e}")
            continue
        
        sim_id: str = item[1]
        
        logger.info(f"Processing simulation with ID: {sim_id}")
        try:
            db: Session = DbSession()
            sim_svc = SimulationService(db, redis)
            
            sim: models.Simulation | None = sim_svc.get_simulation(uuid.UUID(sim_id))
            if sim is None:
                logger.error(f"Simulation ID {sim_id} from queue not found in database. Continuing.")
                continue
            
            # mark simulation as in progress and flush to avoid other worker picking it up
            sim.status = models.SimulationState.RUNNING
            sim.started_at = datetime.now()
            db.flush()
            
            logger.debug(f"Running simulation with ID: {sim_id}")
            sim_result = run_simulation(
                logger, uuid.UUID(sim_id),
                sim.velocity, sim.rpm, sim.friction, sim.launch_angle, sim.lateral_offset)
            logger.debug(f"Run completed for simulation with ID: {sim_id}")
            
            # populate results and mark simulation as completed
            sim.completed_at = datetime.now()
            sim.status = models.SimulationState.COMPLETED
            
            # NOTE: Sim inconsistently returns some values as numpy floats and others as native Python floats
            # TO be safe and future-proof, casting all number values to native type explicitly before passing to DB
            sim.results = models.SimulationResult(
                simulation_id=sim.id,
                execution_duration=float(sim_result['simulation_metadata']['execution_duration_ms']),
                pins_knocked=int(sim_result['simulation_results']['pins_knocked']),
                impact_velocity=float(sim_result['trajectory_analysis']['impact_velocity_ms']),
                hook_potential=float(sim_result['trajectory_analysis']['hook_potential_cm']),
                entry_angle=float(sim_result['trajectory_analysis']['entry_angle_deg']),
                ball_deflection=float(sim_result['trajectory_analysis']['ball_deflection_cm']),
                trajectory_length=float(sim_result['trajectory_analysis']['trajectory_length_m']),
                pin_states=[
                    models.PinState(
                        pin_number=int(pin['pin_number']),
                        knocked=bool(pin['knocked']),
                        impact_velocity=float(pin['impact_velocity_ms']) if pin.get('impact_velocity_ms') is not None else None
                    ) for pin in sim_result['simulation_results']['pin_states']
                ]
            )
            
            sim.telemetry = [
                models.Telemetry(
                    time=float(telemetry['time_s']),
                    position_x=float(telemetry['position_m']['x']),
                    position_y=float(telemetry['position_m']['y']),
                    velocity_x=float(telemetry['velocity_ms']['x']),
                    velocity_y=float(telemetry['velocity_ms']['y']),
                    speed=float(telemetry['speed_ms']),
                    
                    # TODO - looks like this may be an int - also may never vary - evaluate how or if to include
                    rotation=float(telemetry['rotation_rpm']),
                ) for telemetry in sim_result['telemetry']
            ]
            
            # for readability - redundant since auto-flush will happen in finally-commit() below
            db.flush()
        except Exception as e:
            logger.error(f"Error running simulation with ID: {sim_id}. Error: {e}")
            sim.completed_at = None
            sim.status = models.SimulationState.FAILED
            sim.error_msg = str(e)
            sim.results = None
            sim.telemetry = None
            continue
        finally:
            db.commit()
            db.close()
        
        # log success and go around again
        logger.info(f"Completed simulation with ID: {sim_id}")
        logger.info(f"count(telemetry points): {len(sim_result['telemetry'])}, " +
                    f"execution_duration_ms: {sim_result['simulation_metadata']['execution_duration_ms']}, " +
                    f"pins_knocked: {sim_result['simulation_results']['pins_knocked']}, " +
                    f"impact_velocity_ms: {sim_result['trajectory_analysis']['impact_velocity_ms']}, " +
                    f"hook_potential_cm: {sim_result['trajectory_analysis']['hook_potential_cm']}, " +
                    f"entry_angle_deg: {sim_result['trajectory_analysis']['entry_angle_deg']}, " +
                    f"ball_deflection_cm: {sim_result['trajectory_analysis']['ball_deflection_cm']}, " +
                    f"trajectory_length_m: {sim_result['trajectory_analysis']['trajectory_length_m']}")