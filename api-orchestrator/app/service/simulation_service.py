import logging
import uuid

from sqlalchemy.orm import Session
from redis import Redis

from app.config import settings
from app.db import models

class SimulationService:
    """Service layer for managing bowling simulations."""

    def __init__(self, db_session: Session, redis_client: Redis):
        self.db_session = db_session
        self.redis_client = redis_client
        self.logger = logging.getLogger(__name__)

    def create_simulation(self, velocity: float, rpm: int, friction: float, launch_angle: float, lateral_offset: float) -> models.Simulation:
        """Creates & queues a new simulation with the given parameters."""
        self.logger.debug(f"Creating simulation with velocity={velocity}, rpm={rpm}, friction={friction}, launch_angle={launch_angle}, lateral_offset={lateral_offset}")
        
        # add new simulation to the database
        new_simulation = models.Simulation(
            velocity=velocity,
            rpm=rpm,
            friction=friction,
            launch_angle=launch_angle,
            lateral_offset=lateral_offset
        )
        
        # TODO: there is a fail scenario here where DB successfully commits, then we
        # fail to enqueue the job. For production this edges case should be resolved.
        self.db_session.add(new_simulation)
        self.db_session.commit()
        self.db_session.refresh(new_simulation)
        self.logger.info(f"Created new simulation with ID: {new_simulation.id}")
        
        # enqueue the new simulation ID for processing by the worker
        self.redis_client.lpush(settings.queue_name, str(new_simulation.id))
        self.logger.debug(f"Enqueued simulation with ID: {new_simulation.id} for processing.")
        
        return new_simulation

    def get_simulation(self, simulation_id: uuid.UUID) -> models.Simulation | None:
        """Retrieve a simulation by its ID."""
        self.logger.debug(f"Retrieving simulation with ID: {simulation_id}")
        
        simulation = self.db_session.query(models.Simulation).filter_by(id=simulation_id).first()
        if simulation is None:
            self.logger.warning(f"Simulation with ID: {simulation_id} not found.")
        
        return simulation