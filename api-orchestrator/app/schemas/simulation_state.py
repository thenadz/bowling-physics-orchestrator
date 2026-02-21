from enum import Enum


class SimulationState(Enum):
    PENDING = 1
    RUNNING = 2
    COMPLETED = 3
    FAILED = 4