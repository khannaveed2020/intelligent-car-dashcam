from pathlib import Path
from types import SimpleNamespace

import numpy as np

from app.detector import YoloObjectDetector


class FakeModel:
    def predict(self, **_: object) -> list[SimpleNamespace]:
        boxes = [
            SimpleNamespace(cls=np.array([0]), conf=np.array([0.91])),
            SimpleNamespace(cls=np.array([2]), conf=np.array([0.82])),
            SimpleNamespace(cls=np.array([15]), conf=np.array([0.99])),
        ]
        names = {0: "person", 2: "car", 15: "cat"}
        return [SimpleNamespace(boxes=boxes, names=names)]


def test_yolo_detector_retains_only_relevant_labels() -> None:
    detector = YoloObjectDetector()
    detector._model = FakeModel()

    detections = detector.detect(np.zeros((20, 30, 3), dtype=np.uint8))

    assert [(item.label, item.confidence) for item in detections] == [
        ("person", 0.91),
        ("car", 0.82),
    ]


def test_yolo_detector_uses_configured_model_path(monkeypatch, tmp_path: Path) -> None:
    model_path = tmp_path / "models" / "demo.pt"
    monkeypatch.setenv("ROADLENS_MODEL_PATH", str(model_path))

    detector = YoloObjectDetector()

    assert detector.model_name == str(model_path)
