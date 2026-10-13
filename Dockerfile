FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (package + app)
COPY backend/pyproject.toml ./
COPY backend/app ./app
RUN pip install --no-cache-dir .

# Copy the rest of the backend application (alembic, config, etc.)
COPY backend/ .

EXPOSE 8000

# Run migrations, then start the server on Render's $PORT (falls back to 8000)
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
