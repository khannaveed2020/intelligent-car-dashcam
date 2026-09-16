from collections.abc import Sequence
from pathlib import Path

import cv2
import numpy as np
import pytest

from app.models import FrameSample, ObjectDetection
from app.video_processor import (
    VideoProcessingError,
    VideoProcessor,
    VideoValidationError,
    validate_video_file,
)


class FakeCapture:
    def __init__(
        self,
        frames: list[np.ndarray],
        frames_per_second: float = 2.0,
        frame_count: float | None = None,
        opened: bool = True,
    ):
        self.frames = iter(frames)
        self.frames_per_second = frames_per_second
        self.frame_count = float(len(frames)) if frame_count is None else frame_count
        self.opened = opened
        self.released = False

    def isOpened(self) -> bool:
        return self.opened

    def get(self, property_id: int) -> float:
        if property_id == cv2.CAP_PROP_FPS:
            return self.frames_per_second
        if property_id == cv2.CAP_PROP_FRAME_COUNT:
            return self.frame_count
        return 0.0

    def read(self) -> tuple[bool, np.ndarray | None]:
        try:
            return True, next(self.frames)
        except StopIteration:
            return False, None

    def release(self) -> None:
        self.released = True


class FakeDetector:
    def __init__(self, detections: Sequence[ObjectDetection] = ()):
        self.detections = detections
        self.calls = 0

    def detect(self, frame: np.ndarray) -> Sequence[ObjectDetection]:
        self.calls += 1
        return self.detections


def video_file(tmp_path: Path, name: str = "video.mp4") -> Path:
    path = tmp_path / name
    path.write_bytes(b"video")
    return path


def test_iter_samples_uses_configured_timestamps(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    frames = [np.zeros((20, 30, 3), dtype=np.uint8) for _ in range(10)]
    capture = FakeCapture(frames)
    monkeypatch.setattr(cv2, "VideoCapture", lambda _: capture)
    processor = VideoProcessor(FakeDetector(), sample_interval_seconds=2)

    samples = list(processor.iter_samples(video_file(tmp_path)))

    assert [sample.timestamp_seconds for sample in samples] == [0, 2, 4]
    assert capture.released


def test_iter_samples_resizes_wide_frames(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    capture = FakeCapture([np.zeros((600, 1200, 3), dtype=np.uint8)])
    monkeypatch.setattr(cv2, "VideoCapture", lambda _: capture)
    processor = VideoProcessor(FakeDetector(), max_frame_width=960)

    sample = next(processor.iter_samples(video_file(tmp_path)))

    assert sample.image.shape[:2] == (480, 960)


def test_iter_samples_rejects_long_video(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    capture = FakeCapture([], frames_per_second=1, frame_count=121)
    monkeypatch.setattr(cv2, "VideoCapture", lambda _: capture)

    with pytest.raises(VideoValidationError, match="two-minute"):
        list(VideoProcessor(FakeDetector()).iter_samples(video_file(tmp_path)))


def test_iter_samples_rejects_unreadable_video(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(cv2, "VideoCapture", lambda _: FakeCapture([], opened=False))

    with pytest.raises(VideoProcessingError, match="could not be opened"):
        list(VideoProcessor(FakeDetector()).iter_samples(video_file(tmp_path)))


def test_process_creates_one_event_per_unique_label(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    detector = FakeDetector(
        [
            ObjectDetection("car", 0.6),
            ObjectDetection("car", 0.9),
            ObjectDetection("person", 0.8),
        ]
    )
    processor = VideoProcessor(detector)
    sample = FrameSample(2.0, np.zeros((20, 30, 3), dtype=np.uint8))
    monkeypatch.setattr(processor, "iter_samples", lambda _: iter([sample]))
    monkeypatch.setattr(cv2, "imwrite", lambda *_: True)
    progress: list[tuple[int, bool]] = []

    events = processor.process(
        video_file(tmp_path),
        tmp_path / "thumbnails",
        lambda count, complete: progress.append((count, complete)),
    )

    assert [(item.label, item.confidence) for item in events] == [
        ("car", 0.9),
        ("person", 0.8),
    ]
    assert progress == [(1, False), (1, True)]


def test_validate_video_file_rejects_invalid_files(tmp_path: Path) -> None:
    empty = tmp_path / "empty.mp4"
    empty.touch()

    with pytest.raises(VideoValidationError, match="Only MP4"):
        validate_video_file(video_file(tmp_path, "video.mov"))
    with pytest.raises(VideoValidationError, match="empty"):
        validate_video_file(empty)
    with pytest.raises(VideoValidationError, match="100 MB"):
        validate_video_file(video_file(tmp_path), max_size_bytes=1)
