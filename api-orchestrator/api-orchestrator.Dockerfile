FROM python:3.14-slim

WORKDIR /app

COPY ./requirements.txt ./

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r ./requirements.txt

COPY app .

WORKDIR /

# Using just 1 worker for this toy example of gunicorn with a uvicorn worker.
# In "real" production, we would want more workers.
CMD ["gunicorn", "app.main:app", "-c", "app/gunicorn_config.py"]