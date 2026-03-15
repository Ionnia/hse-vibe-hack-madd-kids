from app.schemas.schemas import ChunkPayload


class ChunkingService:
    def chunk(
        self,
        text: str,
        chunk_size: int = 1000,
        overlap: int = 100,
    ) -> list[ChunkPayload]:
        if not text:
            return []

        chunks: list[ChunkPayload] = []
        start = 0
        index = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))

            # Try to break at a sentence or paragraph boundary
            if end < len(text):
                # Look for a newline or period within the last 200 chars of the chunk
                breakpoint = -1
                for i in range(end, max(start, end - 200), -1):
                    if text[i - 1] in (".", "!", "?", "\n"):
                        breakpoint = i
                        break
                if breakpoint > start:
                    end = breakpoint

            chunk_text = text[start:end]

            chunks.append(
                ChunkPayload(
                    chunk_index=index,
                    text=chunk_text,
                    char_start=start,
                    char_end=end,
                    source_asset_id=None,
                )
            )

            index += 1
            next_start = end - overlap
            if next_start <= start:
                next_start = end
            start = next_start

        return chunks
