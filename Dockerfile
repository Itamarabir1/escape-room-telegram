# Build from repo root: docker build -t escape-backend -f Dockerfile .
# Backend runs from /app/backend; REPO root = /app (images, frontend/dist live there).
FROM python:3.11-slim

WORKDIR /app

# Backend code and deps
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend ./backend
COPY images ./images
COPY frontend/dist ./frontend/dist

ENV PYTHONPATH=/app/backend
WORKDIR /app/backend
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
