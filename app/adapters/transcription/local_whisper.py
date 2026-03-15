import io
import logging
import tempfile
import os

from app.adapters.transcription.base import BaseTranscription

logger = logging.getLogger(__name__)


class LocalWhisperTranscription(BaseTranscription):
    """Transcription using faster-whisper running locally."""

    def __init__(self, model_size: str = "base", device: str = "auto", language: str = "ru") -> None:
        self.model_size = model_size
        self.language = language
        self._model = None

        if device == "auto":
            try:
                import torch
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                self.device = "cpu"
        else:
            self.device = device

    def _get_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel
            compute_type = "float16" if self.device == "cuda" else "int8"
            logger.info("Loading faster-whisper model=%s device=%s", self.model_size, self.device)
            self._model = WhisperModel(self.model_size, device=self.device, compute_type=compute_type)
        return self._model

    async def transcribe(self, audio_bytes: bytes) -> str:
        if not audio_bytes:
            return ""

        import asyncio
        return await asyncio.get_event_loop().run_in_executor(None, self._transcribe_sync, audio_bytes)

    def _transcribe_sync(self, audio_bytes: bytes) -> str:
        try:
            model = self._get_model()

            with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
                f.write(audio_bytes)
                tmp_path = f.name

            try:
                segments, info = model.transcribe(
                    tmp_path,
                    language=self.language,
                    beam_size=5,
                )
                text = " ".join(seg.text.strip() for seg in segments)
                logger.info("Transcribed %.1fs audio: %d chars", info.duration, len(text))
                return text
            finally:
                os.unlink(tmp_path)

        except Exception as e:
            logger.error("LocalWhisperTranscription failed: %s", e)
            return ""
