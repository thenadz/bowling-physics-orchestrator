from app.config import settings

bind = "0.0.0.0:80"
accesslog = "-"
access_log_format = settings.log_format
loglevel = settings.log_level.lower()
workers = 1  # For this toy example, we will just use 1 worker. In "real" production, we would want more workers.
worker_class = 'uvicorn_worker.UvicornWorker'