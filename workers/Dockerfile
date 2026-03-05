FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright system dependencies
RUN pip install --no-cache-dir playwright && playwright install --with-deps chromium

COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

RUN pip install --no-cache-dir playwright beautifulsoup4

COPY workers /app/workers
COPY backend /app/backend

ENV PYTHONPATH=/app:/app/backend
