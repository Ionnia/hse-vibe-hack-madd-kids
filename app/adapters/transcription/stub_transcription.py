from app.adapters.transcription.base import BaseTranscription


class StubTranscription(BaseTranscription):
    async def transcribe(self, audio_bytes: bytes) -> str:
        return "[Transcription stub] Audio transcribed text placeholder. In production, this would use Whisper or similar."
