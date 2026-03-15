import base64
import logging

from openai import AsyncOpenAI

from app.adapters.ocr.base import BaseOCR

logger = logging.getLogger(__name__)


class OpenAIOCR(BaseOCR):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def extract_text(self, image_bytes: bytes) -> str:
        if not image_bytes:
            return ""

        b64 = base64.b64encode(image_bytes).decode("utf-8")

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "Извлеки весь текст с этого изображения. "
                                    "Если на изображении учебный материал — формулы, схемы, таблицы — "
                                    "опиши их текстом. Верни только извлечённый текст без комментариев."
                                ),
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                            },
                        ],
                    }
                ],
                max_tokens=2000,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error("OpenAIOCR failed: %s", e)
            return ""
