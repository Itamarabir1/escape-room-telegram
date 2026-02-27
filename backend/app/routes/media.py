# pyright: reportMissingImports=false
"""Serves static media: room images, door video, science lab, lore audio. Paths from paths.py."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from paths import IMAGES_DIR, LORE_WAV_PATH, ROOM_ASSETS_DIR

router = APIRouter(tags=["media"])


@router.get("/room/escape_room.png")
async def serve_room_image():
    """Serves the static room image from project images folder (escape_room.png)."""
    path = IMAGES_DIR / "escape_room.png"
    if not path.exists():
        candidates = sorted(
            IMAGES_DIR.glob("escape_room_*.png"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        path = candidates[0] if candidates else None
    if not path or not path.exists():
        raise HTTPException(
            status_code=404,
            detail="Room image not found. Add images/escape_room.png",
        )
    return FileResponse(path, media_type="image/png")


@router.get("/room/door_open.mp4")
async def serve_door_video():
    """Serves the door opening video from backend/room_assets or images/."""
    for base in (ROOM_ASSETS_DIR, IMAGES_DIR):
        for name in ("door_open.mp4", "door-opening.mp4"):
            path = base / name
            if path.exists():
                return FileResponse(path, media_type="video/mp4")
    raise HTTPException(
        status_code=404,
        detail="Door video not found. Add backend/room_assets/door_open.mp4",
    )


@router.get("/room/science_lab_room.png")
async def serve_science_lab_room():
    """Serves the science lab room image from backend/room_assets or images/."""
    for base in (ROOM_ASSETS_DIR, IMAGES_DIR):
        for name in ("science_lab_room.png", "science_lab.png"):
            path = base / name
            if path.exists():
                return FileResponse(path, media_type="image/png")
        candidates = sorted(
            base.glob("science_lab_room_*.png"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if candidates:
            return FileResponse(candidates[0], media_type="image/png")
    raise HTTPException(
        status_code=404,
        detail="Science lab image not found. Add backend/room_assets/science_lab_room.png",
    )


@router.get("/audio/lore.wav")
async def serve_lore_audio():
    """Serves the static lore audio (backend/audio/lore.wav). Used when user clicks התחל."""
    if not LORE_WAV_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="Lore audio not found. Add backend/audio/lore.wav",
        )
    return FileResponse(LORE_WAV_PATH, media_type="audio/wav")
