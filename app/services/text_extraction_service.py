from app.adapters.ocr.base import BaseOCR
from app.adapters.storage.local import LocalStorage
from app.adapters.transcription.base import BaseTranscription
from app.core.constants import InputType
from app.core.config import settings
from app.models.models import MaterialAsset


def _default_ocr() -> BaseOCR:
    if settings.llm_provider == "openai" and settings.llm_api_key:
        from app.adapters.ocr.openai_ocr import OpenAIOCR
        return OpenAIOCR(api_key=settings.llm_api_key, model="gpt-4o-mini")
    from app.adapters.ocr.stub_ocr import StubOCR
    return StubOCR()


def _default_transcription() -> BaseTranscription:
    backend = settings.transcription_backend
    if backend == "local_whisper":
        from app.adapters.transcription.local_whisper import LocalWhisperTranscription
        return LocalWhisperTranscription(model_size=settings.whisper_model_size)
    if backend == "whisper_api" and settings.llm_api_key:
        from app.adapters.transcription.whisper_transcription import WhisperTranscription
        return WhisperTranscription(api_key=settings.llm_api_key)
    from app.adapters.transcription.stub_transcription import StubTranscription
    return StubTranscription()


class TextExtractionService:
    def __init__(
        self,
        ocr: BaseOCR | None = None,
        transcription: BaseTranscription | None = None,
        storage: LocalStorage | None = None,
    ) -> None:
        self.ocr = ocr or _default_ocr()
        self.transcription = transcription or _default_transcription()
        self.storage = storage or LocalStorage()

    async def extract(self, asset: MaterialAsset) -> str:
        if asset.input_type == InputType.text:
            return asset.extracted_text or ""

        if asset.file_path:
            data = await self.storage.load(asset.file_path)
        else:
            data = b""

        if asset.input_type == InputType.image:
            return await self.ocr.extract_text(data)
        elif asset.input_type == InputType.audio:
            return await self.transcription.transcribe(data)

        return ""
