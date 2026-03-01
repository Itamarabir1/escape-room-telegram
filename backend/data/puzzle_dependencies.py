# pyright: reportMissingImports=false
"""Puzzle dependency rules: which item_id can be solved only after others.
Used by game_action_service to enforce order (e.g. control panel only after clock).
Per-room mapping for future multi-room support."""

# item_id -> list of item_ids that must be SOLVED before this one can be solved
PUZZLE_DEPENDENCIES: dict[str, list[str]] = {
    "board_servers": ["clock_1"],
}

# Human-readable message when dependency is not met (key = dependent item_id)
DEPENDENCY_BLOCK_MESSAGES: dict[str, str] = {
    "board_servers": "כוונו את השעון כדי לפתוח את לוח הבקרה.",
}


def get_puzzle_dependencies(room_id: str | None = None) -> dict[str, list[str]]:
    """Return dependencies for the given room. For now only demo room is supported; room_id ignored."""
    return dict(PUZZLE_DEPENDENCIES)


def get_dependencies_for_item(item_id: str, room_id: str | None = None) -> list[str]:
    """Return list of item_ids that must be solved before item_id can be solved."""
    deps = get_puzzle_dependencies(room_id)
    return list(deps.get(item_id) or [])


def get_block_message(item_id: str) -> str:
    """Return user-facing message when item_id is blocked by unmet dependencies."""
    return DEPENDENCY_BLOCK_MESSAGES.get(
        item_id, "יש לפתור קודם חידות אחרות בחדר."
    )
