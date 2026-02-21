from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.db.models import Base

engine = create_engine(
    settings.db_url
)

# Create all tables associated with Base.metadata in the database
# TODO: for production, need to leverage Alembic for proper incremental migrations
Base.metadata.create_all(engine)

DbSession = sessionmaker(
  bind=engine,
  autocommit=False,
  autoflush=False
)