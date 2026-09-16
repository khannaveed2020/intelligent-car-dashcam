"""Safe video validation, frame sampling, and event generation."""

from collections.abc import Callable, Iterator
from pathlib import Path

import cv2

from app.detector import ObjectDetector
from app.models import DetectedEvent, FrameSample

MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024
MAX_DURATION_SECONDS = 120.0
DEFAULT_SAMPLE_INTERVAL_SECONDS = 2.0
DEFAULT_MAX_FRAME_WIDTH = 960


class VideoProcessingError(RuntimeError):
    """Raised when uploaded video content cannot be processed."""


class VideoValidationError(ValueError):
    """Raised when a video violates an upload constraint."""


def validate_video_file(path: Path, max_size_bytes: int = MAX_FILE_SIZE_BYTES) -> None:
    """Validate the filesystem-level constraints for an uploaded video."""
    if path.suffix.lower() != ".mp4":
        raise VideoValidationError("Only MP4 videos are supported for this demo.")
    if not path.is_file():
        raise VideoValidationError("The uploaded video could not be found.")
    if path.stat().st_size == 0:
        raise VideoValidationError("The uploaded video is empty.")
    if path.stat().st_size > max_size_bytes:
        raise VideoValidationError("The uploaded video exceeds the 100 MB limit.")


class VideoProcessor:
    """Sample a video incrementally and create searchable object events."""

    def __init__(
        self,
        detector: ObjectDetector,
        sample_interval_seconds: float = DEFAULT_SAMPLE_INTERVAL_SECONDS,
        max_duration_seconds: float = MAX_DURATION_SECONDS,
        max_frame_width: int = DEFAULT_MAX_FRAME_WIDTH,
    ):
        if sample_interval_seconds <= 0:
            raise ValueError("Sample interval must be greater than zero.")
        if max_frame_width <= 0:
            raise ValueError("Maximum frame width must be greater than zero.")
        self.detector = detector
        self.sample_interval_seconds = sample_interval_seconds
        self.max_duration_seconds = max_duration_seconds
        self.max_frame_width = max_frame_width

    def _resize_frame(self, frame: cv2.typing.MatLike) -> cv2.typing.MatLike:
        height, width = frame.shape[:2]
        if width <= self.max_frame_width:
            return frame
        scale = self.max_frame_width / width
        return cv2.resize(
            frame,
            (self.max_frame_width, round(height * scale)),
            interpolation=cv2.INTER_AREA,
        )

    def iter_samples(self, video_path: Path) -> Iterator[FrameSample]:
        validate_video_file(video_path)
        capture = cv2.VideoCapture(str(video_path))
        if not capture.isOpened():
            capture.release()
            raise VideoProcessingError("The MP4 could not be opened. Try another video.")

        try:
            frames_per_second = float(capture.get(cv2.CAP_PROP_FPS))
            frame_count = float(capture.get(cv2.CAP_PROP_FRAME_COUNT))
            if frames_per_second <= 0:
                raise VideoProcessingError("The video has invalid frame-rate metadata.")

            duration_seconds = frame_count / frames_per_second if frame_count > 0 else 0.0
            if duration_seconds > self.max_duration_seconds:
                raise VideoValidationError("The video exceeds the two-minute demo limit.")

            frame_index = 0
            next_sample_seconds = 0.0
            decoded_any_frame = False
            while True:
                success, frame = capture.read()
                if not success:
                    break
                decoded_any_frame = True
                timestamp_seconds = frame_index / frames_per_second
                if timestamp_seconds + (0.5 / frames_per_second) >= next_sample_seconds:
                    yield FrameSample(
                        timestamp_seconds=timestamp_seconds,
                        image=self._resize_frame(frame),
                    )
                    next_sample_seconds += self.sample_interval_seconds
                frame_index += 1

            if not decoded_any_frame:
                raise VideoProcessingError("The MP4 contains no readable video frames.")
        finally:
            capture.release()

    def process(
        self,
        video_path: Path,
        thumbnail_dir: Path,
        progress_callback: Callable[[int, bool], None] | None = None,
    ) -> list[DetectedEvent]:
        thumbnail_dir.mkdir(parents=True, exist_ok=True)
        events: list[DetectedEvent] = []
        sample_number = 0
        for sample_number, sample in enumerate(self.iter_samples(video_path), start=1):
            detections = self.detector.detect(sample.image)
            strongest_by_label = {
                label: max(
                    detection.confidence
                    for detection in detections
                    if detection.label.lower() == label
                )
                for label in {detection.label.lower() for detection in detections}
            }
            if strongest_by_label:
                thumbnail_path = thumbnail_dir / f"frame_{sample.timestamp_seconds:08.2f}.jpg"
                if not cv2.imwrite(str(thumbnail_path), sample.image):
                    raise VideoProcessingError("A result thumbnail could not be saved.")
                for label, confidence in sorted(strongest_by_label.items()):
                    events.append(
                        DetectedEvent(
                            timestamp_seconds=sample.timestamp_seconds,
                            label=label,
                            description=f"{label.title()} detected",
                            confidence=confidence,
                            thumbnail_path=str(thumbnail_path),
                        )
                    )
            if progress_callback is not None:
                progress_callback(sample_number, False)

        if progress_callback is not None:
            progress_callback(sample_number, True)
        return events
