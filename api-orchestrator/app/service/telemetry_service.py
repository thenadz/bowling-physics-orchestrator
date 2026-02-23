import logging
import uuid

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.db.models import Simulation, SimulationResult, Telemetry
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
    
    def get_telemetry(self, simulation_id: uuid.UUID, stride: int = 10) -> list[Telemetry]:
        """
        Retrieve the telemetry data for a given simulation ID, with optional downsampling.
        Uses server-side window function filtering for performance on large datasets.
        """
        self.logger.debug(f"Retrieving telemetry for simulation ID: {simulation_id} with stride: {stride}")
        
        # Raw SQL with CTE and window function - server-side filtering
        query = text("""
            WITH ranked AS (
                SELECT *,
                       ROW_NUMBER() OVER (ORDER BY time) as rn
                FROM telemetry
                WHERE simulation_id = :sim_id
            )
            SELECT simulation_id, time, position_x, position_y, velocity_x, velocity_y, speed, rotation
            FROM ranked
            WHERE rn % :stride = 0
            ORDER BY time
        """)
        
        results = self.db_session.execute(query, {"sim_id": simulation_id, "stride": stride}).fetchall()
        
        # Convert rows to Telemetry objects
        telemetry_list = [
            Telemetry(
                simulation_id=row.simulation_id,
                time=row.time,
                position_x=row.position_x,
                position_y=row.position_y,
                velocity_x=row.velocity_x,
                velocity_y=row.velocity_y,
                speed=row.speed,
                rotation=row.rotation
            )
            for row in results
        ]
        
        self.logger.debug(f"Retrieved {len(telemetry_list)} telemetry points.")
        
        return telemetry_list