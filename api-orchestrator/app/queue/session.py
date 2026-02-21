from redis import Redis
from app.config import settings

# TODO - consider using a connection pool for better performance in production environment
RedisSession = Redis(host=settings.queue_host, port=settings.queue_port, decode_responses=True)