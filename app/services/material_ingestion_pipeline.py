from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.storage.local import LocalStorage
from app.core.constants import InputType, MaterialStatus
from app.models.models import StudyMaterial
from app.repositories.repos import AssetRepository, MaterialRepository
from app.services.file_ingestion_service import FileIngestionService
from app.services.text_extraction_service import TextExtractionService


class MaterialIngestionPipeline:
    def __init__(self, session: AsyncSession, storage: LocalStorage | None = None) -> None:
        self.session = session
        self.storage = storage or LocalStorage()
        self.material_repo = MaterialRepository(session)
        self.asset_repo = AssetRepository(session)
        self.file_ingestion = FileIngestionService(session, self.storage)
        self.text_extraction = TextExtractionService(storage=self.storage)

    async def ingest(
        self,
        user_id: UUID,
        input_type: InputType,
        data: bytes | None = None,
        filename: str | None = None,
        telegram_file_id: str | None = None,
        raw_text: str | None = None,
        title: str | None = None,
    ) -> StudyMaterial:
        material = await self.material_repo.create(user_id=user_id, title=title)

        await self.material_repo.update_status(material.id, MaterialStatus.parsing)

        # Create asset
        asset = await self.file_ingestion.save_asset(
            material_id=material.id,
            input_type=input_type,
            data=data,
            filename=filename,
            telegram_file_id=telegram_file_id,
        )

        # If raw text was provided directly (text type), store it on the asset
        if raw_text is not None:
            asset.extracted_text = raw_text
            await self.session.flush()

        # Extract text from asset
        extracted = await self.text_extraction.extract(asset)
        asset.extracted_text = extracted
        await self.session.flush()

        # Update material with raw text
        combined_text = raw_text or extracted
        await self.material_repo.update_texts(material.id, raw_text=combined_text)
        await self.material_repo.update_status(material.id, MaterialStatus.parsed)

        # Reload material
        updated = await self.material_repo.get_by_id(material.id)
        return updated or material
