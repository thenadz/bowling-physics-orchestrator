"""Example unit test for TelemetryService."""
import pytest

from app.service.telemetry_service import TelemetryService
from app.db.models import Simulation, SimulationResult
from app.schemas.simulation_state import SimulationState
from datetime import datetime
import uuid


@pytest.mark.unit
class TestTelemetryService:
    """Test cases for TelemetryService."""

    def test_get_avg_pins_by_velocity(self, test_db_session):
        """Test retrieving average pins knocked by velocity range."""
        # TODO: Implement test
        pass

    def test_get_avg_pins_by_velocity_no_results(self, test_db_session):
        """Test querying velocity range with no simulation results."""
        # TODO: Implement test
        pass
