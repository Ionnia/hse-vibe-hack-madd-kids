import io
import logging

from openai import AsyncOpenAI

from app.adapters.transcription.base import BaseTranscription

logger = logging.getLogger(__name__)


class WhisperTranscription(BaseTranscription):
    def __init__(self, api_key: str) -> None:
        self.client = AsyncOpenAI(api_key=api_key)

    async def transcribe(self, audio_bytes: bytes) -> str:
        if not audio_bytes:
            return ""

        try:
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "audio.ogg"

            response = await self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="ru",
            )
            return response.text or ""
        except Exception as e:
            logger.error("WhisperTranscription failed: %s", e)
            return ""
