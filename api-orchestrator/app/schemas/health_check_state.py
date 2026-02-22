from enum import StrEnum


class HealthCheckState(StrEnum):
    ALIVE = "alive"
    READY = "ready"
    NOT_READY = "not_ready"