from enum import Enum


class HealthCheckState(Enum):
    ALIVE = 1
    READY = 2
    NOT_READY = 3