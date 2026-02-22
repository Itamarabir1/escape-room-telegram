# pyright: reportMissingImports=false
"""Serves the game Web App page (HTML). Health is in routes/health.py."""
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import FileResponse

# Project layout: telegram-bot/{backend,frontend}; backend serves built frontend from frontend/dist
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
FRONTEND_DIST = _REPO_ROOT / "frontend" / "dist"
INDEX_HTML = FRONTEND_DIST / "index.html"

router = APIRouter(tags=["pages"])


@router.get("/game")
async def get_game():
    """Serves the game Web App (HTML) from frontend/dist. Build first: cd frontend && npm run build."""
    if not INDEX_HTML.exists():
        return {"detail": "קובץ המשחק לא נמצא. הרץ קודם: cd frontend && npm run build."}
    return FileResponse(INDEX_HTML)
