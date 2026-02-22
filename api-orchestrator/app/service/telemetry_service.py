import logging

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import Simulation, SimulationResult
from app.schemas.simulation_state import SimulationState
from app.schemas.telemetry import VelocityBucket

class TelemetryService:
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.logger = logging.getLogger(__name__)


    def get_avg_pins_by_velocity(self, min_velocity: float, max_velocity: float) -> VelocityBucket:
        """Calculate the average pins knocked down for a specific velocity range."""
        count, avg = self.db_session.query(
            func.count(Simulation.id),
            func.avg(SimulationResult.pins_knocked)).join(SimulationResult).filter(
            Simulation.velocity >= min_velocity,
            Simulation.velocity <= max_velocity,
            Simulation.status == SimulationState.COMPLETED
        ).one()
        
        return VelocityBucket(
            min_velocity=min_velocity,
            max_velocity=max_velocity,
            average_pins=avg,
            simulation_count=count
        )