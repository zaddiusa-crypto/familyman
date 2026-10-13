FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (package + app)
COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir .

# Copy the rest of the application (alembic, config, etc.)
COPY . .

EXPOSE 8000

# Start the server on Render's $PORT (falls back to 8000); the schema is
# created automatically on startup via Base.metadata.create_all (SQLite).
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
