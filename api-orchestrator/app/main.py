from fastapi import FastAPI

from app.core.logging import configure_logging
from app.api import routes

configure_logging()
# TODO - uvicorn currently ignores all logging config - no pass through from gunicorn
# For now using the default logging which does not match sim-worker

app = FastAPI()
app.include_router(routes.router)