import logging
import json
import uuid
from datetime import datetime
import tempfile
from pathlib import Path
from app.sim.bowling.sim import BowlingSimulation
from app.schemas.bowling_config import BowlingConfig
from app.schemas.simulation_results import BowlingSimulationResults

def run_simulation(id: uuid.UUID, velocity: float, rpm: int, friction: float, launch_angle: float, lateral_offset: float, logger: logging.Logger | None = None) -> BowlingSimulationResults:
    # collect baseline codefied as the example JSON for our BowlingConfig model
    # this is the identical sample JSON originally shipped with sim.py
    json_dict = BowlingConfig.model_json_schema()['example']
    
    # tweak baseline, injecting the values different from example JSON
    json_dict['simulation_metadata']['operator'] = "dan-simulation-driver"
    
    # per run variables
    json_dict['simulation_metadata']['scenario_id'] = f"sim-{id}"
    json_dict['simulation_metadata']['timestamp'] = datetime.now().isoformat()
    json_dict['ball_parameters']['initial_velocity_ms'] = velocity
    json_dict['ball_parameters']['rotational_speed_rpm'] = rpm
    json_dict['ball_parameters']['launch_angle_deg'] = launch_angle
    json_dict['lane_conditions']['friction_coefficient'] = friction
    json_dict['release_point']['lateral_offset_m'] = lateral_offset
    
    json_str: str = json.dumps(json_dict, indent=2)
    
    if logger is not None:
        logger.debug(f"Running simulation with config:\n{json_str}")
    
    # since required sim interface requires file I/O, cleanest option
    # is to use a temp file that'll get cleaned up automatically
    with tempfile.NamedTemporaryFile(mode='w+t') as tf:
        tf.write(json_str)
        tf.flush()
        
        sim = BowlingSimulation(Path(tf.name))
    
    sim_result: dict = sim.run() # type: ignore - sim.py is not typed and we don't have control to add types there, so using dict here for now since we know sim returns a JSON-like dict structure
    
     # validate against our Pydantic model - will raise if any issues with sim output structure
    parsed: BowlingSimulationResults = BowlingSimulationResults.model_validate(sim_result)
    
    return parsed