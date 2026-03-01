"""Health routes: endpoint definitions only."""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from api.controllers.health_controller import health_check

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return await health_check()
