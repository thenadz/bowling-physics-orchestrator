"""Shared test fixtures for common test data and mocks."""
import uuid
from datetime import datetime

import pytest

from app.db.models import Simulation, SimulationResult
from app.schemas.simulation_state import SimulationState


@pytest.fixture
def sample_simulation(test_db_session):
    """Create a sample pending simulation."""
    sim = Simulation(
        id=uuid.uuid7(),
        velocity=15.0,
        rpm=100,
        friction=0.5,
        launch_angle=0.0,
        lateral_offset=0.0,
        status=SimulationState.PENDING,
        queued_at=datetime.now()
    )
    test_db_session.add(sim)
    test_db_session.commit()
    return sim


@pytest.fixture
def sample_completed_simulation_with_results(test_db_session):
    """Create a completed simulation with results."""
    sim = Simulation(
        id=uuid.uuid7(),
        velocity=15.0,
        rpm=100,
        friction=0.5,
        launch_angle=0.0,
        lateral_offset=0.0,
        status=SimulationState.COMPLETED,
        queued_at=datetime.now(),
        completed_at=datetime.now()
    )
    test_db_session.add(sim)
    test_db_session.flush()

    results = SimulationResult(
        simulation_id=sim.id,
        execution_duration=123.45,
        pins_knocked=8,
        impact_velocity=12.5,
        hook_potential=0.3,
        entry_angle=5.2,
        ball_deflection=8.1,
        trajectory_length=18.5
    )
    test_db_session.add(results)
    test_db_session.commit()
    return sim
