from abc import ABC, abstractmethod


class BaseStorage(ABC):
    @abstractmethod
    async def save(self, file_id: str, data: bytes, filename: str) -> str:
        """Save data and return storage path."""
        ...

    @abstractmethod
    async def load(self, path: str) -> bytes:
        """Load data from storage path."""
        ...
