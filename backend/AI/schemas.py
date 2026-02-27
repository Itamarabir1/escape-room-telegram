# pyright: reportMissingImports=false
"""
Pydantic schemas for AI-generated room (e.g. future dynamic room creation).
Not used at runtime; API and game state use domain/game.py (TypedDict) as source of truth.
Kept for reference / future use.
"""
from pydantic import BaseModel, Field
from typing import List


class RoomItem(BaseModel):
    id: str
    label: str
    x: int = Field(description="Position from 0 to 100")
    y: int = Field(description="Position from 0 to 100")
    action_type: str = Field(description="e.g., 'collect', 'examine', 'unlock'")

class EscapeRoom(BaseModel):
    room_name: str
    description: str
    lore: str = Field(description="Dramatic 2-sentence back-story in Hebrew for voice-over")
    visual_prompt: str = Field(description="Prompt for image generation")
    items: List[RoomItem]


class EscapeRoomResponse(BaseModel):
    room_details: EscapeRoom
    image_url: str