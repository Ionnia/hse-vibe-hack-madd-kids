from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.db.session import get_session

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@router.get("/ready")
async def ready(session: AsyncSession = Depends(get_session)) -> dict:
    try:
        await session.execute(text("SELECT 1"))
        return {"status": "ready", "database": "ok"}
    except Exception as e:
        return {"status": "not_ready", "database": str(e)}
