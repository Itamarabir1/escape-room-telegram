# pyright: reportMissingImports=false
"""Domain schema for game session. Shared contract for API responses and application layer."""
from typing import Any
from typing_extensions import NotRequired, TypedDict  # pyright: ignore[reportMissingModuleSource]


class RoomItemResponse(TypedDict):
    id: str
    label: str
    x: int
    y: int
    action_type: str


class PuzzleResponse(TypedDict):
    """Task for a room item. unlock = has answer to submit; examine = backstory only. correct_answer never sent to client."""
    item_id: str
    type: str  # "unlock" | "examine"
    backstory: str
    encoded_clue: NotRequired[str]
    prompt_text: NotRequired[str]


class GameStateResponse(TypedDict):
    """Response shape for GET /api/games/{game_id}. Used by API and frontend contract."""
    game_id: str
    players: dict[str, str]  # JSON: user_id as string -> name
    game_active: bool
    # AI room or demo room (filled on first load or when demo=1)
    room_image_url: NotRequired[str]
    room_image_width: NotRequired[int]
    room_image_height: NotRequired[int]
    room_name: NotRequired[str]
    room_description: NotRequired[str]
    room_lore: NotRequired[str]
    room_items: NotRequired[list[RoomItemResponse]]
    puzzle: NotRequired[PuzzleResponse]  # deprecated: use puzzles
    puzzles: NotRequired[list[PuzzleResponse]]  # one per clickable item


class HealthResponse(TypedDict):
    """Response shape for GET /health. Used by health route and external scripts."""
    status: str
    mode: str
