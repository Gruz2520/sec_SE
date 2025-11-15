# syntax=docker/dockerfile:1.7

FROM python:3.11-slim AS build

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt pyproject.toml ./

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir=/wheels -r requirements.txt

FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN groupadd -r appuser && \
    useradd -r -g appuser -u 1000 appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

COPY --from=build /wheels /wheels

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir /wheels/* && \
    rm -rf /wheels

COPY --chown=appuser:appuser . .

USER appuser

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=2).read()" || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
