import logging
import sys

from app.config import settings

LOG_LEVEL = settings.log_level.upper()
LOG_FORMAT = settings.log_format

def configure_logging():
    """Setup central logging configuration"""
    root = logging.getLogger()
    root.setLevel(LOG_LEVEL)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(LOG_FORMAT)
    handler.setFormatter(formatter)
    root.addHandler(handler)



