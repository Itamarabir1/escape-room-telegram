# pyright: reportMissingImports=false
"""Game API service: demo room application and GameStateResponse building. Used by app/api/games.py."""
import logging
from typing import Any

from config.config import config
from data.demo_room import (
    DEMO_ROOM_HEIGHT,
    DEMO_ROOM_ITEMS,
    DEMO_ROOM_META,
    DEMO_ROOM_PUZZLES,
    DEMO_ROOM_WIDTH,
)
from domain.game import GameStateResponse, PuzzleResponse
from domain.puzzle_status import PuzzleStatus
from utils.puzzle import SAFE_BACKSTORY

logger = logging.getLogger(__name__)


def apply_demo_room(game: dict[str, Any]) -> None:
    """Inject demo room items, puzzles, and static room image URL. Mutates game in place.
    room_image_url must point to the API (backend) that serves /room/escape_room.png, not the frontend."""
    api_base = (config.VITE_API_URL or "http://localhost:8000").strip().rstrip("/")
    game["room_image_url"] = f"{api_base}/room/escape_room.png"
    game["room_image_width"] = DEMO_ROOM_WIDTH
    game["room_image_height"] = DEMO_ROOM_HEIGHT
    game["room_name"] = DEMO_ROOM_META["room_name"]
    game["room_description"] = DEMO_ROOM_META["room_description"]
    game["room_lore"] = DEMO_ROOM_META.get("room_lore", "")
    game["room_items"] = [dict(it) for it in DEMO_ROOM_ITEMS]
    game["room_puzzles"] = {}
    for item_id, p in DEMO_ROOM_PUZZLES.items():
        game["room_puzzles"][item_id] = dict(p)


def needs_demo_room(game: dict[str, Any]) -> bool:
    """True when room data is missing or incomplete (same logic as get_game_state)."""
    return (
        not game.get("room_image_url")
        or len(game.get("room_items") or []) < len(DEMO_ROOM_ITEMS)
        or not game.get("room_image_width")
    )


def build_game_state_response(game_id: str, game: dict[str, Any]) -> GameStateResponse:
    """Build GameStateResponse dict from game state (after demo room applied if needed)."""
    players_raw = game.get("players", {})
    players_str: dict[str, str] = {str(k): v for k, v in players_raw.items()}
    out: GameStateResponse = {
        "game_id": game_id,
        "players": players_str,
        "game_active": game.get("game_active", True),
    }
    if game.get("door_opened"):
        out["door_opened"] = bool(game.get("door_opened"))
    if game.get("room_image_url") or game.get("room_items"):
        if game.get("room_image_url"):
            out["room_image_url"] = game["room_image_url"]
            out["room_image_width"] = game.get("room_image_width") or DEMO_ROOM_WIDTH
            out["room_image_height"] = game.get("room_image_height") or DEMO_ROOM_HEIGHT
        out["room_name"] = game.get("room_name", "")
        out["room_description"] = game.get("room_description", "")
        out["room_lore"] = game.get("room_lore", "")
        items_raw = game.get("room_items") or []
        out["room_items"] = [
            {
                "id": it["id"],
                "label": it["label"],
                "x": it["x"],
                "y": it["y"],
                "action_type": it.get("action_type", "examine"),
            }
            for it in items_raw
        ]
        puzzles_raw = game.get("room_puzzles") or {}
        puzzles_list: list[PuzzleResponse] = []
        first_unlock: PuzzleResponse | None = None
        for item_id, p in puzzles_raw.items():
            ptype = p.get("type") or ("unlock" if p.get("correct_answer") else "examine")
            pr: PuzzleResponse = {
                "item_id": item_id,
                "type": ptype,
                "backstory": p.get("backstory", SAFE_BACKSTORY),
            }
            if p.get("encoded_clue"):
                pr["encoded_clue"] = p["encoded_clue"]
            if p.get("prompt_text"):
                pr["prompt_text"] = p["prompt_text"]
            puzzles_list.append(pr)
            if ptype == "unlock" and first_unlock is None:
                first_unlock = pr
        out["puzzles"] = puzzles_list
        if first_unlock:
            out["puzzle"] = first_unlock
        room_solved = game.get("room_solved") or {}
        out["solved_item_ids"] = [
            iid for iid, status in room_solved.items()
            if status == PuzzleStatus.SOLVED.value
        ]
        if game.get("started_at"):
            out["started_at"] = game["started_at"]
    return out


def item_label(game: dict[str, Any], item_id: str) -> str:
    """Get display label for room item; fallback to item_id."""
    for it in game.get("room_items") or []:
        if it.get("id") == item_id:
            return (it.get("label") or item_id).strip()
    return item_id


def all_unlock_puzzles_solved(game: dict[str, Any]) -> bool:
    """True if every unlock puzzle in room_puzzles is marked SOLVED in room_solved."""
    puzzles = game.get("room_puzzles") or {}
    room_solved = game.get("room_solved") or {}
    for item_id, p in puzzles.items():
        if (p.get("type") or "").lower() == "unlock":
            if room_solved.get(item_id) != PuzzleStatus.SOLVED.value:
                return False
    return True
