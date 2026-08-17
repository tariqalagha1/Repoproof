FROM python:3.12-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]" || pip install --no-cache-dir \
    fastapi>=0.115.0 \
    uvicorn[standard]>=0.30.0 \
    sqlalchemy[asyncio]>=2.0.35 \
    asyncpg>=0.30.0 \
    alembic>=1.13.0 \
    pydantic>=2.9.0 \
    pydantic-settings>=2.6.0 \
    httpx>=0.28.0 \
    python-dotenv>=1.0.0 \
    openai>=1.55.0 \
    pytest>=8.3.0 \
    pytest-asyncio>=0.24.0 \
    httpx>=0.28.0

# Copy source
COPY . .

# Run alembic migration then start the server
CMD sh -c "cd /app && python -m alembic -c alembic.ini upgrade head && \
    python -m uvicorn src.main:app --host 0.0.0.0 --port 8000"
