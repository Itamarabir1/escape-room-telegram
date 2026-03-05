# pyright: reportMissingImports=false
"""Single place for app URLs. Uses config for base."""
from urllib.parse import quote

from config import config


def game_app_url() -> str:
    """URL of the game Web App page (no game_id). Used by /start button."""
    return f"{config.base_url()}/game"


def game_page_url(game_id: str) -> str:
    """URL of the game page with game_id. Used for 'שחק עכשיו' links."""
    return f"{config.base_url()}/game?game_id={game_id}"


def game_entry_url(game_id: str) -> str:
    """Best entry URL for group buttons: Mini App deep-link when configured."""
    bot_username = (config.TELEGRAM_BOT_USERNAME or "").strip().lstrip("@")
    mini_app_short_name = (config.TELEGRAM_MINI_APP_SHORT_NAME or "").strip().strip("/")
    if bot_username and mini_app_short_name:
        encoded_game_id = quote(str(game_id), safe="")
        return f"https://t.me/{bot_username}/{mini_app_short_name}?startapp={encoded_game_id}"
    return game_page_url(game_id)
