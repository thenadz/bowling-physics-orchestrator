import logging

from collections.abc import Generator
from fastapi import Depends
from redis import Redis
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.service.simulation_service import SimulationService

from app.db.session import DbSession
from app.queue.session import RedisSession

logger = logging.getLogger(__name__)

def get_db() -> Generator[Session, None, None]:
    db: Session = DbSession()
    try:
        yield db
    finally:
        db.close()

def get_redis() -> Generator[Redis, None, None]:
    redis: Redis = RedisSession
    try:
        yield redis
    finally:
        redis.close()

def get_simulation_service(db: Session = Depends(get_db), redis: Redis = Depends(get_redis)) -> SimulationService:
    return SimulationService(db, redis)

def get_health(db: Session = Depends(get_db), redis: Redis = Depends(get_redis)) -> bool:
    """Simple dependency to check if we can connect to the database and Redis."""
    ret = True
    try:
        # Try a simple query to check DB connectivity
        db.execute(text("SELECT 1"))
    except Exception as e:
        # Log the exception for debugging purposes
        logger.warning(f"Not healthy yet. Database connection error: {e}")
        ret = False
    
    try:        # Try a simple command to check Redis connectivity
        redis.ping()
    except Exception as e:
        # Log the exception for debugging purposes
        logger.warning(f"Not healthy yet. Redis connection error: {e}")
        ret = False
    
    return ret