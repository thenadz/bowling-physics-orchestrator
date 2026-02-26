import logging

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session

from app.config import settings
from app.db.models import Base

logger = logging.getLogger(__name__)

# TODO - lazy singleton pattern avoids startup race condition, however there is
# still a risk of runtime connection issues in event of transient DB failure.
# For production deployent, this will require furhter hardening.
_engine: Engine | None = None
_db_session: sessionmaker[Session] | None = None

def get_engine() -> Engine:
    global _engine
    if _engine is None:
        # args tell libpq to set session timezones
        # NOTE: for SQLite, timezone handling is different and this won't have the intended effect
        _engine = create_engine(settings.db_url, connect_args={"options": "-c timezone=utc"})
        logger.info("Database engine created successfully.")
        
        # Create all tables associated with Base.metadata in the database
        # TODO: for production, need to leverage Alembic for proper incremental migrations
        try:
            Base.metadata.create_all(_engine)
        except Exception as e:
            logger.critical(f"Error creating database tables: {e}")
    
    return _engine

def get_db_session() -> sessionmaker[Session]:
    global _db_session
    if _db_session is None:
        _db_session = sessionmaker(bind=get_engine(), autocommit=False, autoflush=False)
    return _db_session