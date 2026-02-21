from enum import Enum

class AppStatus(Enum):
    STARTING = 1
    RUNNING = 2
    STOPPING = 3
    STOPPED = 4