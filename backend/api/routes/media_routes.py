# pyright: reportMissingImports=false
"""Media routes: endpoint definitions only."""
from fastapi import APIRouter

from api.controllers.media_controller import (
    serve_room_image,
    serve_door_video,
    serve_science_lab_room,
    serve_lore_audio,
)

router = APIRouter(tags=["media"])


@router.get("/room/escape_room.png")
async def room_image():
    return await serve_room_image()


@router.get("/room/door_open.mp4")
async def door_video():
    return await serve_door_video()


@router.get("/room/science_lab_room.png")
async def science_lab_room():
    return await serve_science_lab_room()


@router.get("/audio/lore.wav")
async def lore_audio():
    return await serve_lore_audio()
