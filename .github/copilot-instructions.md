# Intelligent Car Dashcam development instructions

## Product goal
Build a privacy-conscious MVP that analyzes uploaded dashcam MP4 files and returns searchable, timestamped object detections.

## Engineering principles
- Use Python 3.11+ and type annotations for public functions.
- Keep UI, video processing, detection, and search logic separated.
- Prefer small, testable functions and explicit data models.
- Validate external input and surface actionable errors.
- Never commit uploaded videos, generated images, model weights, or secrets.
- Do not implement identity inference or claim collision, intent, proximity, direction, or color detection.

## Application conventions
- Streamlit is the user interface.
- OpenCV performs video reading and frame extraction.
- The object detector is injectable and mocked in tests.
- Streamlit session state stores active demo results.
- Tests must not download or load real model weights.
