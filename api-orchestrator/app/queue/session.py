from redis import Redis, ConnectionPool
from app.config import settings


pool = ConnectionPool(
  host=settings.queue_host,
  password=settings.queue_password,
  port=settings.queue_port,
  decode_responses=True)

RedisSession = Redis(connection_pool=pool)