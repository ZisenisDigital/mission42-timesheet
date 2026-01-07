FROM python:3.11-slim

WORKDIR /app

# Install uv package manager
RUN pip install --no-cache-dir uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY app ./app
COPY scripts ./scripts

# Install dependencies
RUN uv sync --frozen

# Create logs directory
RUN mkdir -p /app/logs

# Expose FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run migrations and seeds on startup, then start API
CMD ["sh", "-c", "uv run python scripts/seed_settings.py && uv run python scripts/seed_work_packages.py && uv run python scripts/seed_project_specs.py && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000"]
