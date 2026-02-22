"""Pytest configuration and shared fixtures."""
import os
import sys

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Add app to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db.models import Base


@pytest.fixture(scope="session")
def test_db_engine():
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def test_db_session(test_db_engine) -> Session:
    """Create a fresh database session for each test."""
    connection = test_db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    # TODO: Implement with fakeredis or similar
    pass
