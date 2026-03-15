from abc import ABC, abstractmethod


class BaseTranscription(ABC):
    @abstractmethod
    async def transcribe(self, audio_bytes: bytes) -> str:
        """Transcribe audio bytes to text."""
        ...
