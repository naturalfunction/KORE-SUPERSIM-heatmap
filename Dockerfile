# syntax=docker/dockerfile:1

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

# System deps (curl for healthchecks/debug)
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (better layer caching)
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copy application code
COPY app ./app
COPY templates ./templates
COPY static ./static
COPY README.md ./README.md

# Create a place for SQLite db when using a container volume
RUN mkdir -p /data

EXPOSE 8000

# Default DB is local SQLite unless overridden via env
# Note: DATABASE_URL is read inside app/core/db.py

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
