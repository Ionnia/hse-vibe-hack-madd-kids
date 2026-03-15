import os
from pathlib import Path

import aiofiles

from app.adapters.storage.base import BaseStorage
from app.core.config import settings


class LocalStorage(BaseStorage):
    def __init__(self, base_path: str | None = None) -> None:
        self.base_path = Path(base_path or settings.storage_local_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def save(self, file_id: str, data: bytes, filename: str) -> str:
        subdir = self.base_path / file_id
        subdir.mkdir(parents=True, exist_ok=True)
        file_path = subdir / filename
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(data)
        return str(file_path)

    async def load(self, path: str) -> bytes:
        async with aiofiles.open(path, "rb") as f:
            return await f.read()
