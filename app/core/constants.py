from enum import Enum


class MaterialStatus(str, Enum):
    uploaded = "uploaded"
    parsing = "parsing"
    parsed = "parsed"
    normalizing = "normalizing"
    normalized = "normalized"
    extracting = "extracting"
    topics_extracted = "topics_extracted"
    ready = "ready"
    failed = "failed"


class TaskType(str, Enum):
    flash = "flash"
    exercise = "exercise"


class ReviewVerdict(str, Enum):
    correct = "correct"
    incorrect = "incorrect"
    partial = "partial"


class ProgressLevel(str, Enum):
    unknown = "unknown"
    weak = "weak"
    learning = "learning"
    good = "good"
    mastered = "mastered"


class InputType(str, Enum):
    image = "image"
    audio = "audio"
    text = "text"


class SubjectType(str, Enum):
    math = "math"
    physics = "physics"
    chemistry = "chemistry"
    biology = "biology"
    programming = "programming"
    language = "language"
    other = "other"
