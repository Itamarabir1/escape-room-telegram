# Build from repo root with dockerContext: . (e.g. docker build -f backend/Dockerfile .).
# The images/ directory must exist at repo root (copied as ./images/).
FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY backend/ ./backend/
COPY images/ ./images/

# Single tool for deps: uv (pyproject.toml + uv.lock). No pip/requirements.txt.
ENV UV_LINK_MODE=copy
ENV UV_NO_DEV=1
WORKDIR /app/backend
RUN uv sync --locked

# Run as non-root user.
RUN adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app
USER appuser

WORKDIR /app/backend
ENV PYTHONPATH=/app/backend
ENV PATH="/app/backend/.venv/bin:$PATH"

EXPOSE 8000

# PORT is set by Render or docker-compose.
# timeout-keep-alive 0: keep long-lived SSE connections open.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --timeout-keep-alive 0"]
