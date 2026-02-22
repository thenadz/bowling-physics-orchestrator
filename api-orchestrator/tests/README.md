# Unit Testing

This directory contains the test suite for the bowling-physics-orchestrator API.

## Structure

```
tests/
├── conftest.py              # Pytest configuration and shared fixtures
├── pytest.ini               # Pytest settings
├── unit/                    # Unit tests (no external dependencies)
│   ├── api/                 # API endpoint tests
│   ├── service/             # Service layer tests
│   ├── db/                  # Database layer tests
│   └── core/                # Core module tests
├── integration/             # Integration tests (with real/test databases)
└── fixtures/                # Shared test data and mock factories
    └── models.py            # Fixtures for creating test data
```

## Running Tests

### All tests
```bash
pytest
```

### Unit tests only
```bash
pytest -m unit
```

### Integration tests only
```bash
pytest -m integration
```

### Specific test file
```bash
pytest tests/unit/service/test_telemetry_service.py
```

### With coverage
```bash
pytest --cov=app --cov-report=html
```

## Dependencies

Add these to your `requirements.txt`:
```
pytest==7.x
pytest-asyncio==0.21.x
pytest-cov==4.x
pytest-mock==3.x
sqlalchemy==2.x
```

## Writing Tests

### Unit Test Example
```python
def test_my_function(test_db_session):
    # Setup
    sim = Simulation(...)
    test_db_session.add(sim)
    test_db_session.commit()
    
    # Execute
    result = my_service.do_something(sim.id)
    
    # Assert
    assert result == expected
```

### Using Fixtures
```python
def test_with_sample_data(sample_completed_simulation_with_results):
    # sample_completed_simulation_with_results is already in the database
    sim = sample_completed_simulation_with_results
    assert sim.status == SimulationState.COMPLETED
```
