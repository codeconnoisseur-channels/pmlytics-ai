FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies first for efficient layer caching
COPY pyproject.toml .
COPY README.md .
RUN pip install --no-cache-dir -e .

# Copy application source code
COPY . .

# Expose default port (overridden dynamically at runtime by cloud platform via $PORT)
EXPOSE 8000

# Execute database migrations if DATABASE_URL is set, then launch FastAPI via uvicorn
CMD ["sh", "-c", "if [ -n \"$DATABASE_URL\" ]; then python -m alembic upgrade head; fi && python -m uvicorn app.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
