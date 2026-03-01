# pyright: reportMissingImports=false
"""Page routes: endpoint definitions only."""
from fastapi import APIRouter, Request

from api.controllers.pages_controller import get_game_page

router = APIRouter(tags=["pages"])


@router.get("/game")
async def game(request: Request):
    return await get_game_page(request)
