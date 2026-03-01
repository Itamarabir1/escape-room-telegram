# pyright: reportMissingImports=false
"""Single place for app URLs. Uses config for base."""
from config.config import config


def game_app_url() -> str:
    """URL of the game Web App page (no game_id). Used by /start button."""
    return f"{config.base_url()}/game"


def game_page_url(game_id: str) -> str:
    """URL of the game page with game_id. Used for 'שחק עכשיו' links."""
    return f"{config.base_url()}/game?game_id={game_id}"
