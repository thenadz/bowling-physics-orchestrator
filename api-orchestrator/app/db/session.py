import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.db.models import Base

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.db_url
)

# Create all tables associated with Base.metadata in the database
# TODO: for production, need to leverage Alembic for proper incremental migrations
Base.metadata.create_all(engine)
logger.info("Database tables created successfully.")

DbSession = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)