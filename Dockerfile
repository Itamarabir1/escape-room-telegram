# Build from repo root: docker build -t escape-backend -f Dockerfile .
# אותו UV + pyproject.toml כמו locally – בלי requirements.txt.
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

# התקנת תלויות מ־pyproject.toml (ו־uv.lock אם קיים)
COPY pyproject.toml uv.lock* ./
COPY backend ./backend
RUN uv sync --frozen --no-dev --no-install-project || uv sync --no-dev --no-install-project

# קבצי אפליקציה
COPY images ./images
COPY frontend/dist ./frontend/dist

ENV PYTHONPATH=/app/backend
WORKDIR /app/backend
EXPOSE 8000

# הרצה עם UV כמו ב-local
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
