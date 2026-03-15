from app.core.constants import InputType

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".tif"}
AUDIO_EXTENSIONS = {".mp3", ".mp4", ".ogg", ".wav", ".m4a", ".flac", ".aac", ".opus", ".oga"}

IMAGE_MIMES = {
    "image/jpeg", "image/png", "image/gif", "image/bmp", "image/webp", "image/tiff",
}
AUDIO_MIMES = {
    "audio/mpeg", "audio/mp4", "audio/ogg", "audio/wav", "audio/x-wav",
    "audio/m4a", "audio/flac", "audio/aac", "audio/opus",
}


class InputClassifier:
    def classify_by_extension(self, filename: str) -> InputType:
        ext = ""
        if "." in filename:
            ext = "." + filename.rsplit(".", 1)[-1].lower()
        if ext in IMAGE_EXTENSIONS:
            return InputType.image
        if ext in AUDIO_EXTENSIONS:
            return InputType.audio
        return InputType.text

    def classify_by_mime(self, mime_type: str) -> InputType:
        mime = mime_type.lower().split(";")[0].strip()
        if mime in IMAGE_MIMES:
            return InputType.image
        if mime in AUDIO_MIMES:
            return InputType.audio
        return InputType.text

    def classify(self, filename: str | None = None, mime_type: str | None = None) -> InputType:
        if mime_type:
            result = self.classify_by_mime(mime_type)
            if result != InputType.text:
                return result
        if filename:
            return self.classify_by_extension(filename)
        return InputType.text


input_classifier = InputClassifier()
