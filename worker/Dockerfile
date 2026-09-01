FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends stockfish && \
    rm -rf /var/lib/apt/lists/*

RUN adduser --gecos="" docker

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

USER docker

COPY tasks.py .
COPY models.py .
COPY database.py .

CMD ["celery", "-A", "tasks", "worker", "--loglevel=info"]
