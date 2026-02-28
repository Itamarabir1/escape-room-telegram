# pyright: reportMissingImports=false
"""Project path constants. Single place for media and static dirs. Used by main and routes/media."""
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _BACKEND_DIR.parent

IMAGES_DIR = _REPO_ROOT / "images"
ROOM_ASSETS_DIR = _BACKEND_DIR / "room_assets"
AUDIO_DIR = _BACKEND_DIR / "audio"

LORE_WAV_PATH = AUDIO_DIR / "lore.wav"
