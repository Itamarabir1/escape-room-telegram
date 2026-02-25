## השתמש בגרסה יציבה של uv
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

# קביעת תיקיית העבודה לשורש הפרויקט
WORKDIR /app

# 1. העתקת קבצי התלויות לשורש לצורך ה-Sync
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project || uv sync --no-dev --no-install-project

# 2. העתקת הקבצים - שים לב שאנחנו שומרים על המבנה שהקוד מצפה לו
COPY backend ./backend
COPY images ./images
COPY frontend/dist ./frontend/dist

# 3. הגדרת PYTHONPATH כך שפייתון יזהה גם את תיקיית backend כשורש של מודולים
# זה פותר את הבעיה ש-main.py מנסה לייבא מ-app.bot או config ישירות
ENV PYTHONPATH=/app/backend:/app
EXPOSE 8000

# 4. פקודת ההרצה המתוקנת:
# אנחנו מריצים את uvicorn מתוך /app ומצביעים על המיקום המדויק של ה-app בתוך תיקיית backend
CMD ["sh", "-c", "uv run uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]