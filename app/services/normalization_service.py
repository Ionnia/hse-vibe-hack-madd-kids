import re


class NormalizationService:
    def normalize(self, text: str) -> str:
        if not text:
            return ""

        # Strip leading/trailing whitespace
        text = text.strip()

        # Remove common OCR artifacts (ligatures, weird chars)
        text = text.replace("\x00", "")
        text = text.replace("\ufffd", "")
        text = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

        # Normalize Unicode whitespace to ASCII space (except newlines/tabs)
        text = re.sub(r"[^\S\n\r\t]", " ", text)

        # Collapse multiple spaces/tabs within lines
        lines = text.splitlines()
        cleaned: list[str] = []
        for line in lines:
            line = re.sub(r"[ \t]+", " ", line).strip()
            cleaned.append(line)

        # Collapse more than 2 consecutive blank lines
        result: list[str] = []
        empty_count = 0
        for line in cleaned:
            if line == "":
                empty_count += 1
                if empty_count <= 2:
                    result.append(line)
            else:
                empty_count = 0
                result.append(line)

        return "\n".join(result)
