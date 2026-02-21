from enum import Enum


class HealthCheckState(Enum):
    ALIVE = 1
    READY = 2