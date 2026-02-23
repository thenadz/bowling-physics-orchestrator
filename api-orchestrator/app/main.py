from fastapi import FastAPI

from app.core.logging import configure_logging

from app.api.auth import router as auth_router
from app.api.rest import router as rest_router
from app.api.graphql import router as graphql_router

from prometheus_fastapi_instrumentator import Instrumentator

configure_logging()
# TODO - uvicorn currently ignores all logging config - no pass through from gunicorn
# For now using the default logging which does not match sim-worker

# build our routes for both REST and GraphQL endpoints
app = FastAPI()
app.include_router(auth_router)
app.include_router(rest_router)
app.include_router(graphql_router, prefix="/graphql")

# TODO - while this has successfully created a prometheus endpoint, which upon
# manual inspection is working, we do not yet have a good visualization layer setup.
# To verify, simply visit http://localhost:8000/metrics
Instrumentator().instrument(app).expose(app, include_in_schema=True, should_gzip=True)