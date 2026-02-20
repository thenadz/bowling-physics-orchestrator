import uuid

from fastapi import FastAPI
from pydantic import Field
from app.schemas.bowling_config import BowlingConfig

app = FastAPI()

# Requirement: Submit bowling config (velocity, RPM, friction, angle) and queue job
@app.post("/simulations")
async def create_simulation(config: BowlingConfig):
    # Logic to create a new simulation
    simulation_id: uuid.UUID = Field(default_factory=uuid.uuid7)  # Placeholder for actual simulation ID generation
    state = "queued"  # Placeholder for actual job queuing logic
    return {"simulation_id": simulation_id, "state": state}

# Requirement: Query job state (pending/running/completed/failed) with metadata
@app.get("/simulations/{simulation_id}")
async def get_simulation(simulation_id: uuid.UUID):
    # Logic to retrieve a simulation by its ID
    return {"simulation_id": simulation_id, "state": "TODO"}

# Requirement: Retrieve pins knocked, hook potential, impact velocity, execution time
@app.get("/simulations/{simulation_id}/results")
async def get_simulation_results(simulation_id: uuid.UUID):
    # Logic to retrieve results of a simulation by its ID
    return {"simulation_id": simulation_id, "results": "TODO"}

# Requirement: Retrieve full trajectory data with downsampling options
@app.get("/telemetry/{simulation_id}")
async def get_telemetry(simulation_id: uuid.UUID):
    # Logic to retrieve telemetry data of a simulation by its ID
    return {"simulation_id": simulation_id, "telemetry": "TODO"}

# Requirement: service up (if we get here, we're alive)
@app.get("/health/live")
def health_live():
    # Logic to check the health of the application
    return {"status": "alive"}

# Requirement: dependencies available
@app.get("/health/ready")
async def health_ready():
    # Logic to check if the application is ready to handle requests
    return {"status": "ready"}