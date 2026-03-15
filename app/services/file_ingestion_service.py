from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.storage.local import LocalStorage
from app.core.constants import InputType
from app.models.models import MaterialAsset
from app.repositories.repos import AssetRepository


class FileIngestionService:
    def __init__(self, session: AsyncSession, storage: LocalStorage | None = None) -> None:
        self.session = session
        self.storage = storage or LocalStorage()
        self.asset_repo = AssetRepository(session)

    async def save_asset(
        self,
        material_id: UUID,
        input_type: InputType,
        data: bytes | None,
        filename: str | None,
        telegram_file_id: str | None = None,
    ) -> MaterialAsset:
        file_path: str | None = None
        if data and filename:
            file_path = await self.storage.save(
                file_id=str(material_id),
                data=data,
                filename=filename,
            )

        asset = await self.asset_repo.create(
            material_id=material_id,
            input_type=input_type,
            file_path=file_path,
            telegram_file_id=telegram_file_id,
        )
        return asset
