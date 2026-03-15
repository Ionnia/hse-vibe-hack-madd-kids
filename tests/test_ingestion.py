import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import InputType, MaterialStatus
from app.repositories.repos import UserRepository
from app.services.material_ingestion_pipeline import MaterialIngestionPipeline


@pytest.mark.asyncio
async def test_text_ingestion_pipeline(session: AsyncSession, tmp_path):
    user_repo = UserRepository(session)
    user = await user_repo.create(telegram_id=7001001)
    await session.flush()

    from app.adapters.storage.local import LocalStorage
    storage = LocalStorage(base_path=str(tmp_path))
    pipeline = MaterialIngestionPipeline(session, storage=storage)

    material = await pipeline.ingest(
        user_id=user.id,
        input_type=InputType.text,
        raw_text="This is a test study material about mathematics and algebra.",
        title="Test Material",
    )
    await session.commit()

    assert material is not None
    assert material.raw_text == "This is a test study material about mathematics and algebra."
    assert material.status == MaterialStatus.parsed


@pytest.mark.asyncio
async def test_image_ingestion_pipeline(session: AsyncSession, tmp_path):
    user_repo = UserRepository(session)
    user = await user_repo.create(telegram_id=7001002)
    await session.flush()

    from app.adapters.storage.local import LocalStorage
    storage = LocalStorage(base_path=str(tmp_path))
    pipeline = MaterialIngestionPipeline(session, storage=storage)

    fake_image_bytes = b"\xff\xd8\xff" + b"\x00" * 100  # fake JPEG header
    material = await pipeline.ingest(
        user_id=user.id,
        input_type=InputType.image,
        data=fake_image_bytes,
        filename="test.jpg",
        title="Test Image",
    )
    await session.commit()

    assert material is not None
    assert material.status == MaterialStatus.parsed


@pytest.mark.asyncio
async def test_ingestion_creates_asset(session: AsyncSession, tmp_path):
    user_repo = UserRepository(session)
    user = await user_repo.create(telegram_id=7001003)
    await session.flush()

    from app.adapters.storage.local import LocalStorage
    from app.repositories.repos import AssetRepository
    storage = LocalStorage(base_path=str(tmp_path))
    pipeline = MaterialIngestionPipeline(session, storage=storage)

    material = await pipeline.ingest(
        user_id=user.id,
        input_type=InputType.text,
        raw_text="Study content for testing assets",
    )
    await session.flush()

    asset_repo = AssetRepository(session)
    assets = await asset_repo.get_by_material_id(material.id)
    assert len(assets) == 1
    assert assets[0].input_type == InputType.text
