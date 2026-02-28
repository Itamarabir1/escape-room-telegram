# Build from repo root: docker build -f backend/Dockerfile .
FROM python:3.11-slim

WORKDIR /app

COPY backend/ ./backend/
COPY images/ ./images/

RUN pip install --no-cache-dir -r backend/requirements.txt

WORKDIR /app/backend
ENV PYTHONPATH=/app/backend

EXPOSE 8000

# PORT is set by Render or docker-compose
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
