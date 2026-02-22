from fastapi import FastAPI

from app.core.logging import configure_logging

from app.api.rest import router as rest_router
from app.api.graphql import router as graphql_router

configure_logging()
# TODO - uvicorn currently ignores all logging config - no pass through from gunicorn
# For now using the default logging which does not match sim-worker

# build our routes for both REST and GraphQL endpoints
app = FastAPI()
app.include_router(rest_router)
app.include_router(graphql_router, prefix="/graphql")
