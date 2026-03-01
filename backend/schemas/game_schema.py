# pyright: reportMissingImports=false
"""API request/response validation schemas (Pydantic). Used by FastAPI routes."""
from pydantic import BaseModel, Field


class GameActionRequest(BaseModel):
    """Request body for POST /api/games/{game_id}/action."""

    item_id: str = Field(..., min_length=1, description="Room item / puzzle id")
    answer: str = Field(default="", description="Player's answer")
    solver_name: str | None = Field(default=None, description="Display name of solver")


class OkResponse(BaseModel):
    """Common response for POST start, time_up, door_opened."""

    ok: bool = True
    message: str | None = None


class GameActionResponse(BaseModel):
    """Response for POST /api/games/{game_id}/action."""

    ok: bool = True
    game_id: str = ""
    correct: bool = False
    message: str = ""
