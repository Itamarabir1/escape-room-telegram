# Build from repo root: docker build -t escape-backend -f Dockerfile .
# שורש הפרויקט במיכל = /app. הרצה כ-backend.app.main:app מ-WORKDIR /app.
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

# 1. העתקת הגדרות תלויות בלבד (לניצול cache של דוקר)
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project || uv sync --no-dev --no-install-project

# 2. העתקת שאר קבצי האפליקציה בנתיבים המקוריים
COPY backend ./backend
COPY images ./images
COPY frontend/dist ./frontend/dist

# 3. PYTHONPATH: /app ל-backend.app.main, /app/backend ל-config ו-app
ENV PYTHONPATH=/app:/app/backend
EXPOSE 8000

# 4. הרצה משורש הפרויקט (/app). PORT מ-Render, ברירת מחדל 8000 ל-docker/local
CMD ["sh", "-c", "uv run uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
