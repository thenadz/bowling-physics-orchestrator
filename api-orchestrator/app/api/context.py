from fastapi import Depends
from strawberry.fastapi import BaseContext

from app.service.telemetry_service import TelemetryService
from app.api.deps import get_telemetry_service

class CustomContext(BaseContext):
    """Custom context to bridge between FastAPI DI and Strawberry GraphQL."""
    def __init__(self, telemetry_service: TelemetryService):
        self.telemetry_service = telemetry_service

async def get_context(telemetry_service: TelemetryService = Depends(get_telemetry_service)) -> CustomContext:
    """Leverage FastAPI DI to get TelemetryService with backing DB session"""
    return CustomContext(telemetry_service=telemetry_service)
