from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.repositories.repos import MaterialRepository
from app.schemas.schemas import MaterialRead

router = APIRouter(prefix="/materials", tags=["materials"])


@router.get("", response_model=list[MaterialRead])
async def list_materials(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> list[MaterialRead]:
    repo = MaterialRepository(session)
    materials = await repo.get_by_user_id(user_id)
    return [MaterialRead.model_validate(m) for m in materials]


@router.get("/{material_id}", response_model=MaterialRead)
async def get_material(
    material_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> MaterialRead:
    repo = MaterialRepository(session)
    material = await repo.get_by_id(material_id)
    if material is None:
        raise HTTPException(status_code=404, detail="Material not found")
    return MaterialRead.model_validate(material)


@router.get("/{material_id}/status")
async def get_material_status(
    material_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> dict:
    repo = MaterialRepository(session)
    material = await repo.get_by_id(material_id)
    if material is None:
        raise HTTPException(status_code=404, detail="Material not found")
    return {"material_id": str(material_id), "status": material.status.value}
