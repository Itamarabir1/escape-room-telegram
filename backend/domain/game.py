# pyright: reportMissingImports=false
"""Domain schema for game session. TypedDict response shapes shared by API and application layer."""
from typing import Any
from typing_extensions import NotRequired, TypedDict  # pyright: ignore[reportMissingModuleSource]


class RoomItemResponse(TypedDict):
    id: str
    label: str
    x: int
    y: int
    action_type: str


class PuzzleResponse(TypedDict):
    item_id: str
    type: str
    backstory: str
    encoded_clue: NotRequired[str]
    prompt_text: NotRequired[str]


class GameStateResponse(TypedDict):
    game_id: str
    players: dict[str, str]
    game_active: bool
    room_image_url: NotRequired[str]
    room_image_width: NotRequired[int]
    room_image_height: NotRequired[int]
    room_name: NotRequired[str]
    room_description: NotRequired[str]
    room_lore: NotRequired[str]
    room_items: NotRequired[list[RoomItemResponse]]
    puzzle: NotRequired[PuzzleResponse]
    puzzles: NotRequired[list[PuzzleResponse]]
    solved_item_ids: NotRequired[list[str]]
    door_opened: NotRequired[bool]
    started_at: NotRequired[str]


class HealthResponse(TypedDict):
    status: str
    mode: str
