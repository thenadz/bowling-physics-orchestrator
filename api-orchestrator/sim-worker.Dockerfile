FROM python:3.14-slim

WORKDIR /app

COPY ./requirements.txt ./

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r ./requirements.txt

COPY app .

WORKDIR /

CMD ["python", "-m", "app.sim_main"]