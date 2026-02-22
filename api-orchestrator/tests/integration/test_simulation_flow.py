"""Example integration test for full API flow."""
import pytest
import uuid

from app.schemas.simulation_results import BowlingSimulationResults
from app.sim.sim_harness import run_simulation

@pytest.mark.integration
class TestSimulationFlow:
    """Integration tests for complete simulation workflows."""

    def test_create_and_retrieve_simulation(self):
        """Test creating and retrieving a simulation."""
        # test against config provided with sim.py
        sim: BowlingSimulationResults = run_simulation(uuid.uuid7(), velocity=8.5, rpm=320, friction=0.044, launch_angle=0.3, lateral_offset=0.0)
        
        # test against results provided with sim.py
        assert sim.simulation_results.pins_knocked == 9
        assert sim.trajectory_analysis.impact_velocity_ms == 7.49
        assert sim.trajectory_analysis.hook_potential_cm == 69.6
        assert sim.trajectory_analysis.entry_angle_deg == 0.85
        assert sim.trajectory_analysis.ball_deflection_cm == 12.6
        assert sim.trajectory_analysis.trajectory_length_m == 18.29

    def test_full_simulation_lifecycle(self):
        """Test full simulation from creation to results retrieval."""
        # TODO: Implement test
        pass
