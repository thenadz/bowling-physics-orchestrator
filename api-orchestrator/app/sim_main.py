import uuid
from datetime import datetime
from typing import cast
from sqlalchemy.orm import Session

from app.db import models
from app.db.session import DbSession
from app.queue.session import RedisSession
from app.service.simulation_service import SimulationService
from app.config import settings

if __name__ == "__main__":
  print("Starting simulation worker...", flush=True)
  
  # TODO - consider using a connection pool for better performance in production environment
  redis = RedisSession
  
  # TODO - consider using a more robust worker framework like Celery or RQ for better performance and reliability in production environment
  while True:
    try:
      # block until a new simulation ID is available in the queue
      item: tuple[str, str] | None = cast(tuple[str, str] | None, redis.blpop([settings.queue_name])) # type: ignore
      
      if item is None:
        # TODO - log low priority - no queue items during timeout period. Continuing.
        continue
      
      sim_id: str = item[1]
    except Exception as e:
      # TODO - add error handling and logging here for robustness in production environment
      print(f"Error popping from the queue. Error: {e}")
      continue
    
    try:
      # TODO - add error handling and logging here for robustness in production environment
      print(f"Processing simulation with ID: {sim_id}")
      
      db: Session = DbSession()
      sim_svc = SimulationService(db, redis)
      
      sim: models.Simulation | None = sim_svc.get_simulation(uuid.UUID(sim_id))
      if sim is None:
        # TODO - log error - simulation ID from queue not found in database. Continuing.
        continue
      
      # mark simulation as in progress and flush to avoid someone else picking it up
      sim.status = models.SimulationState.RUNNING
      sim.started_at = datetime.now()
      db.flush()
      
      # TODO - add actual simulation processing logic here, e.g. call a physics engine with the simulation parameters from the database, store results back in the database, etc.
      
      sim.status = models.SimulationState.COMPLETED
      sim.completed_at = datetime.now()
      db.commit()
      print(f"Completed simulation with ID: {sim_id}")
    except Exception as e:
      # TODO - add error handling and logging here for robustness in production environment
      print(f"Error processing simulation with ID: {sim_id}. Error: {e}")
      continue