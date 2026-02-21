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

if __name__ == "__main__":
  configure_logging()
  logger = logging.getLogger("sim-worker")
  
  logger.info("Starting simulation worker...")
  
  # TODO - consider using a connection pool for better performance in production environment
  redis = RedisSession
  
  # TODO - consider using a more robust worker framework like Celery or RQ for better performance and reliability in production environment
  while True:
    try:
      # block until a new simulation ID is available in the queue
      item: tuple[str, str] | None = cast(tuple[str, str] | None, redis.blpop([settings.queue_name], timeout=30)) # type: ignore
      
      if item is None:
        logger.warning("Received null item from queue. Continuing.")
        continue
      
      sim_id: str = item[1]
    except Exception as e:
      logger.error(f"Error popping from the queue. Error: {e}")
      continue
    
    try:
      logger.info(f"Processing simulation with ID: {sim_id}")
      
      db: Session = DbSession()
      sim_svc = SimulationService(db, redis)
      
      sim: models.Simulation | None = sim_svc.get_simulation(uuid.UUID(sim_id))
      if sim is None:
        logger.error(f"Simulation ID {sim_id} from queue not found in database. Continuing.")
        continue
      
      # mark simulation as in progress and flush to avoid someone else picking it up
      sim.status = models.SimulationState.RUNNING
      sim.started_at = datetime.now()
      db.flush()
      
      # TODO - add actual simulation processing logic here, e.g. call a physics engine with the simulation parameters from the database, store results back in the database, etc.
      
      sim.status = models.SimulationState.COMPLETED
      sim.completed_at = datetime.now()
      db.commit()
      logger.info(f"Completed simulation with ID: {sim_id}")
      continue
    except Exception as e:
      logger.error(f"Error processing simulation with ID: {sim_id}. Error: {e}")
      continue