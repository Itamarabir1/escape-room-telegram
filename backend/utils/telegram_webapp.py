# pyright: reportMissingImports=false
"""Validate Telegram Web App initData and extract user id. Used to restrict game access to registered players only."""
import hashlib
import hmac
import json
import logging
from urllib.parse import parse_qs, unquote

logger = logging.getLogger(__name__)

# Max age of initData (seconds). Telegram recommends not accepting data older than a day.
INIT_DATA_MAX_AGE_SECONDS = 86400


def validate_init_data(init_data: str, bot_token: str) -> dict | None:
    """
    Validate Telegram Web App initData string and return parsed payload (with 'user' containing 'id')
    or None if invalid/expired.
    See: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    if not init_data or not init_data.strip() or not bot_token:
        return None
    init_data = init_data.strip()
    try:
        # Parse query string; values can appear multiple times, take first
        parsed = parse_qs(init_data, keep_blank_values=True)
        vals = {k: unquote(v[0]) if v and v[0] else "" for k, v in parsed.items()}
    except Exception as e:
        logger.debug("telegram_webapp: parse init_data failed: %s", e)
        return None
    if "hash" not in vals:
        return None
    received_hash = vals.pop("hash")
    # Build data-check-string: sorted key=value, newline-separated
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(vals.items()))
    # secret_key = HMAC-SHA256(key=bot_token, message=b"WebAppData")
    secret_key = hmac.new(
        bot_token.encode(), b"WebAppData", hashlib.sha256
    ).digest()
    computed_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(computed_hash, received_hash):
        logger.debug("telegram_webapp: hash mismatch")
        return None
    # Optional: check auth_date is not too old
    auth_date_str = vals.get("auth_date") or ""
    if auth_date_str:
        try:
            import time
            auth_date = int(auth_date_str)
            if int(time.time()) - auth_date > INIT_DATA_MAX_AGE_SECONDS:
                logger.debug("telegram_webapp: auth_date too old")
                return None
        except ValueError:
            return None
    return vals


def get_user_id_from_validated(validated: dict) -> int | None:
    """Extract Telegram user id from validated initData payload (user field is JSON string)."""
    user_str = validated.get("user") or ""
    if not user_str:
        return None
    try:
        user = json.loads(user_str)
        return int(user.get("id"))
    except (json.JSONDecodeError, TypeError, ValueError):
        return None
