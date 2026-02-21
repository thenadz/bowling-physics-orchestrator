from collections.abc import Generator
from fastapi import Depends
from redis import Redis
from sqlalchemy.orm import Session

from app.service.simulation_service import SimulationService

from app.db.session import DbSession
from app.queue.session import RedisSession

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

# TODO get telemetry service