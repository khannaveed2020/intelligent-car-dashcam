"""Object detector abstraction and lazy Ultralytics implementation."""

import os
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Protocol

import numpy as np
from numpy.typing import NDArray
from platformdirs import user_cache_path

from app.models import ObjectDetection

RELEVANT_LABELS = frozenset({"person", "bicycle", "car", "motorcycle", "bus", "truck"})


class ObjectDetector(Protocol):
    """Detect relevant objects in a decoded BGR frame."""

    def detect(self, frame: NDArray[np.uint8]) -> Sequence[ObjectDetection]: ...


class YoloObjectDetector:
    """Lazy YOLO adapter that retains only MVP labels."""

    def __init__(self, model_name: str | None = None, confidence_threshold: float = 0.35):
        if not 0 <= confidence_threshold <= 1:
            raise ValueError("Confidence threshold must be between 0 and 1.")
        default_model_path = user_cache_path("roadlens") / "models" / "yolo11n.pt"
        self.model_name = model_name or os.environ.get(
            "ROADLENS_MODEL_PATH", str(default_model_path)
        )
        self.confidence_threshold = confidence_threshold
        self._model: Any | None = None

    def load(self) -> Any:
        """Load or download model weights into a writable location."""
        if self._model is None:
            from ultralytics import YOLO

            Path(self.model_name).parent.mkdir(parents=True, exist_ok=True)
            self._model = YOLO(self.model_name)
        return self._model

    def detect(self, frame: NDArray[np.uint8]) -> list[ObjectDetection]:
        results = self.load().predict(
            source=frame,
            conf=self.confidence_threshold,
            verbose=False,
        )
        detections: list[ObjectDetection] = []
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0].item())
                label = str(result.names[class_id]).lower()
                if label in RELEVANT_LABELS:
                    detections.append(
                        ObjectDetection(label=label, confidence=float(box.conf[0].item()))
                    )
        return detections
