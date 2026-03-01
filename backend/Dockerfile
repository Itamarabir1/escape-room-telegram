# Build from repo root: docker build -f backend/Dockerfile .
FROM python:3.11-slim

WORKDIR /app

COPY backend/ ./backend/
COPY images/ ./images/

# Use a virtual env to avoid "Running pip as the 'root' user" warning and follow best practice
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv /opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip install --no-cache-dir -r backend/requirements.txt

# Run as non-root user
RUN adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app
USER appuser

WORKDIR /app/backend
ENV PYTHONPATH=/app/backend

EXPOSE 8000

# PORT is set by Render or docker-compose
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
