import logging
import uuid

from datetime import datetime
from typing import cast
from sqlalchemy.orm import Session

from app.config import settings
from app.core.logging import configure_logging
from app.db import models
from app.db.session import get_db_session
from app.queue.session import RedisSession
from app.service.simulation_service import SimulationService
from app.sim.sim_harness import run_simulation
from app.schemas.simulation_results import BowlingSimulationResults

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
        
        sim_id: uuid.UUID = uuid.UUID(item[1])
        
        logger.info(f"Processing simulation with ID: {sim_id}")
        sim: models.Simulation | None = None
        db: Session | None = None
        sim_result: BowlingSimulationResults | None = None
        try:
            db = get_db_session()()
            sim_svc = SimulationService(db, redis)
            
            sim = sim_svc.get_simulation(sim_id)
            if sim is None:
                logger.error(f"Simulation ID {sim_id} from queue not found in database. Continuing.")
                continue
            
            # mark simulation as in progress and flush to avoid other worker picking it up
            sim.status = models.SimulationState.RUNNING
            sim.started_at = datetime.now()
            db.flush()
            
            logger.debug(f"Running simulation with ID: {sim_id}")
            sim_result = run_simulation(
                sim_id,
                sim.velocity, sim.rpm, sim.friction, sim.launch_angle, sim.lateral_offset,
                logger)
            logger.debug(f"Run completed for simulation with ID: {sim_id}")
            
            # populate results and mark simulation as completed
            sim.completed_at = datetime.now()
            sim.status = models.SimulationState.COMPLETED
            
            sim.results = models.SimulationResult(
                simulation_id=sim.id,
                execution_duration=sim_result.simulation_metadata.execution_duration_ms,
                pins_knocked=sim_result.simulation_results.pins_knocked,
                impact_velocity=sim_result.trajectory_analysis.impact_velocity_ms,
                hook_potential=sim_result.trajectory_analysis.hook_potential_cm,
                entry_angle=sim_result.trajectory_analysis.entry_angle_deg,
                ball_deflection=sim_result.trajectory_analysis.ball_deflection_cm,
                trajectory_length=sim_result.trajectory_analysis.trajectory_length_m,
                pin_states=[
                    models.PinState(
                        pin_number=pin.pin_number,
                        knocked=pin.knocked,
                        impact_velocity=pin.impact_velocity_ms
                    ) for pin in sim_result.simulation_results.pin_states
                ]
            )
            
            sim.telemetry = [
                models.Telemetry(
                    time=telemetry.time_s,
                    position_x=telemetry.position_m.x,
                    position_y=telemetry.position_m.y,
                    velocity_x=telemetry.velocity_ms.x,
                    velocity_y=telemetry.velocity_ms.y,
                    speed=telemetry.speed_ms,
                    
                    # TODO - looks like this may be an int - also may never vary - evaluate how or if to include
                    rotation=telemetry.rotation_rpm,
                ) for telemetry in sim_result.telemetry
            ]
            
            # for readability - redundant since auto-flush will happen in finally-commit() below
            db.flush()
        except Exception as e:
            logger.error(f"Error running simulation with ID: {sim_id}. Error: {e}")
            if sim is not None:
                # retry - increment retry count until configurable max retries is reached, then mark as failed
                # TODO - exponential backoff and dead-letter queue for failed jobs would be good additions for production environment
                if sim.retry_count > settings.queue_max_retries:
                    logger.error(f"Simulation with ID: {sim_id} has exceeded max retries. Marking as failed.")
                    
                    sim.status = models.SimulationState.FAILED
                    sim.error_msg = f"Exceeded max retries with error: {e}"
                else:
                    logger.info(f"Retrying simulation with ID: {sim_id} (retry count: {sim.retry_count}).")
                    
                    sim.status = models.SimulationState.PENDING
                    sim.error_msg = f"Error on attempt {sim.retry_count} with error: {e}"
                
                sim.retry_count += 1
                sim.completed_at = None
                sim.results = None
                sim.telemetry = []
                
        finally:
            # save off state of ORM before we kill DB connection
            sim_status = sim.status if sim is not None else models.SimulationState.FAILED
            
            # persist sim state & close DB session following above whether happy path or not
            if db is not None:
                db.commit()
                db.close()
            else:
                logger.critical(f"DB session was not available at end of sim loop for simulation with ID: {sim_id}. Unable to commit results.")
                logger.critical(f"Simulation with ID: {sim_id} may be left in an inconsistent state. Manual intervention may be required.")
            
            # if we're retrying, re-queue
            if sim_status == models.SimulationState.PENDING:
                # re-enqueue the new simulation ID for processing by the worker
                redis.lpush(settings.queue_name, str(sim_id))
                logger.info(f"Re-enqueued simulation with ID: {sim_id} for processing.")
                
        
        # log success and go around again
        logger.info(f"Completed simulation with ID: {sim_id}")
        
        if sim_result is None: continue
        logger.info(f"count(telemetry points): {len(sim_result.telemetry)}, " +
                    f"execution_duration_ms: {sim_result.simulation_metadata.execution_duration_ms}, " +
                    f"pins_knocked: {sim_result.simulation_results.pins_knocked}, " +
                    f"impact_velocity_ms: {sim_result.trajectory_analysis.impact_velocity_ms}, " +
                    f"hook_potential_cm: {sim_result.trajectory_analysis.hook_potential_cm}, " +
                    f"entry_angle_deg: {sim_result.trajectory_analysis.entry_angle_deg}, " +
                    f"ball_deflection_cm: {sim_result.trajectory_analysis.ball_deflection_cm}, " +
                    f"trajectory_length_m: {sim_result.trajectory_analysis.trajectory_length_m}")