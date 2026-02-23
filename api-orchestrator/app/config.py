from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Simulation engine configuration
    simulation_engine_url: str = "http://localhost:8001"  # URL of the simulation engine API
    max_simulation_time_ms: int = 10000  # Max allowed simulation time in milliseconds
    
    log_level: str = "INFO"  # Logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL)
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Database configuration for storing results and metadata (currently only PostgreSQL w/ TimescaleDB supported)
    db_url: str = ""  # Database url (e.g., postgresql+psycopg2://user:password@localhost:5432/simulations)
    
    # Queue configuration for sim job management (currently only Redis supported)
    queue_host: str = "localhost"  # Host for the job queue
    queue_port: int = 6379  # Port for the job queue
    queue_name: str = "simulation_jobs"  # Name of the job queue (e.g., Redis queue)
    queue_password: str = ""  # Password for the job queue (if applicable)
    queue_max_retries: int = 3  # Max number of retries for failed jobs
    
    user_secret_key: str = "" # get yours: `openssl rand -hex 32`

    model_config = SettingsConfigDict(env_file=".env.dev")

settings = Settings()