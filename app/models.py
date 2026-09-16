"""Typed domain models for dashcam detections."""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True, slots=True)
class ObjectDetection:
    """A relevant object returned by a detector for one frame."""

    label: str
    confidence: float

    def __post_init__(self) -> None:
        if not self.label.strip():
            raise ValueError("Detection label cannot be empty.")
        if not 0 <= self.confidence <= 1:
            raise ValueError("Detection confidence must be between 0 and 1.")


@dataclass(frozen=True, slots=True)
class FrameSample:
    """A decoded video frame and its position in seconds."""

    timestamp_seconds: float
    image: NDArray[np.uint8]

    def __post_init__(self) -> None:
        if self.timestamp_seconds < 0:
            raise ValueError("Frame timestamp cannot be negative.")


@dataclass(frozen=True, slots=True)
class DetectedEvent:
    """A searchable detection shown in the demo UI."""

    timestamp_seconds: float
    label: str
    description: str
    confidence: float
    thumbnail_path: str

    def __post_init__(self) -> None:
        if self.timestamp_seconds < 0:
            raise ValueError("Event timestamp cannot be negative.")
        if not self.label.strip():
            raise ValueError("Event label cannot be empty.")
        if not 0 <= self.confidence <= 1:
            raise ValueError("Event confidence must be between 0 and 1.")
