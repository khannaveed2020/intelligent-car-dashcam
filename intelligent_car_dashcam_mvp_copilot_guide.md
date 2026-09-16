# Intelligent Car Dashcam — Hackathon MVP Guide

## 1. Project vision

Build a small application that lets a user upload short dashcam footage, find people and vehicles, and retrieve matching moments with simple natural-language queries.

### One-line pitch

> Find people and vehicles in dashcam footage without scrubbing through the entire video.

### Demo promise

For a reliable hackathon demo, make one promise and deliver it end to end:

> Upload a short MP4, search for a person or vehicle, and open the matching moment.

Collision detection, vehicle color, approach direction, and semantic embeddings are stretch goals. A frame-based object detector alone cannot reliably determine impact, motion direction, proximity, or color.

## 2. Recommended MVP

The first version should support two scenarios:

1. **Person and vehicle detection** — find frames containing a person, car, bus, truck, motorcycle, or bicycle.
2. **Deterministic natural-language search** — answer requests such as:
  - “Show me people.”
  - “Find the cars.”
  - “Show all vehicles.”

Use a pre-tested video that contains at least one person and one vehicle. Keep it between 20 and 60 seconds so processing finishes during the demo.

### MVP user journey

1. User uploads an MP4 dashcam video.
2. The application extracts one frame every few seconds.
3. An object-detection component identifies people and vehicles.
4. Detected objects and timestamps are stored for the current video.
5. The user enters a natural-language query.
6. The application returns matching timestamps, thumbnails, confidence scores, and short event descriptions.
7. The user opens the video at the relevant timestamp.

## 3. MVP boundaries

### Include

- MP4 upload
- Local video processing
- Frame and thumbnail extraction
- Detection of people, cars, buses, trucks, motorcycles, and bicycles
- Timestamped event records
- Deterministic keyword search with a small synonym map
- Results page with thumbnails
- Local development environment
- Unit tests for search and sampled-frame timestamps

### Defer until later

- Real-time camera streaming
- Mobile application
- Number-plate recognition
- Face recognition
- Collision or sudden-motion detection
- Vehicle color classification
- Driver-side or approach-direction inference
- Semantic search and embeddings
- Production cloud deployment
- Police, insurance, or emergency-service integration
- Large-scale video storage
- Continuous GPS tracking
- Automatic legal or fault determination

## 4. Suggested technology stack

Use a simple Python-based stack so the team can produce a working demo quickly.

| Area | Suggested choice |
|---|---|
| Language | Python 3.11+ |
| Web UI | Streamlit |
| Video processing | OpenCV |
| Object detection | Ultralytics YOLO (`yolo11n.pt`) |
| Demo state | Streamlit session state |
| Data models | Python dataclasses |
| Testing | pytest |
| Formatting and linting | Ruff |
| Packaging | `pyproject.toml` |

Do not add a database, task queue, API server, cloud dependency, or embeddings to the hackathon MVP. Add them only after the local flow works reliably.

## 5. High-level architecture

```text
User
  |
  v
Streamlit web interface
  |
  +--> Video upload
  |
  +--> Video processing service
          |
          +--> OpenCV frame extraction
          +--> YOLO object detection
          +--> Thumbnail generation
          |
          v
         Session event list
          |
          v
    Deterministic query mapper
  |
  v
Timestamped results, thumbnails, and confidence scores
```

## 6. Recommended repository structure

```text
intelligent-car-dashcam/
├── .github/
│   └── copilot-instructions.md
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── video_processor.py
│   ├── detector.py
│   └── search.py
├── tests/
│   ├── test_search.py
│   └── test_video_processor.py
├── sample_data/
│   └── README.md
├── .gitignore
├── pyproject.toml
└── README.md
```

Do not commit uploaded videos, generated thumbnails, model weights, or secrets.

## 7. Core data model

A detected event only needs the fields displayed or searched by the demo:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class DetectedEvent:
    timestamp_seconds: float
    label: str
    description: str
    confidence: float
    thumbnail_path: str
```

Create one event per sampled frame and detected label. Deduplicate nearby results at search time if necessary; do not build event aggregation until repeated results become a visible demo problem.

## 8. Processing pipeline

### Step 1: Validate the upload

- Accept MP4 initially.
- Limit uploads to 100 MB and reject videos longer than two minutes.
- Generate a unique internal video ID.
- Store the original filename only as metadata.
- Never use the original filename directly as a filesystem path.

### Step 2: Extract frames

- Open the video with OpenCV.
- Read its frame rate and duration.
- Sample a frame every two seconds for the first MVP.
- Resize sampled frames before detection to keep processing predictable.
- Save one thumbnail for each retained result.

### Step 3: Detect objects

For every sampled frame:

- Run the object detector.
- Retain relevant labels: person, bicycle, car, motorcycle, bus, and truck.
- Save label, confidence, timestamp, and thumbnail path.
- Store the resulting events in `st.session_state`.

### Step 4: Search events

The first search implementation can map common words to labels and event types.

Examples:

| Query phrase | Search mapping |
|---|---|
| person, people, someone | `person` |
| car, cars | `car` |
| vehicle, vehicles | `bicycle`, `car`, `motorcycle`, `bus`, `truck` |

Rank matches by timestamp for a clear video timeline. Return an empty list for unsupported queries instead of guessing.

## 9. Definition of done for the MVP

The MVP is complete when:

- A developer can start the app with documented commands.
- A user can upload a sample MP4.
- Processing progress is visible.
- At least people and vehicles are detected.
- Results remain available for the current Streamlit session.
- A user can enter a query and receive relevant results.
- Each result includes a thumbnail, timestamp, event description, and confidence score.
- The page displays the uploaded video and the selected result timestamp.
- Unit tests cover query mapping and sampled-frame timestamps.
- A short demonstration can be completed in under three minutes.
- The app shows an actionable message for invalid video, no detections, and no search results.

## 10. Local setup

### Prerequisites

- Git
- Python 3.11 or later
- Visual Studio Code
- GitHub Copilot and GitHub Copilot Chat extensions

### Initial commands

```bash
git clone <repository-url>
cd intelligent-car-dashcam
python -m venv .venv
```

Activate the environment:

```bash
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS or Linux
source .venv/bin/activate
```

Install the project after `pyproject.toml` has been created:

```bash
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

Run the application:

```bash
streamlit run app/main.py
```

Run validation:

```bash
ruff check .
ruff format --check .
pytest
```

## 11. GitHub Copilot instructions

Create `.github/copilot-instructions.md` with the following content:

```markdown
# Intelligent Car Dashcam development instructions

## Product goal
Build a privacy-conscious MVP that analyzes uploaded dashcam MP4 files and returns searchable, timestamped events.

## Engineering principles
- Use Python 3.11+ and type annotations for public functions.
- Keep UI, video processing, detection, and search logic separated.
- Prefer small, testable functions and explicit data models.
- Validate all external input.
- Do not silently ignore video, model, or filesystem errors.
- Return actionable error messages without exposing sensitive paths or data.
- Never commit uploaded videos, generated images, model weights, or secrets.
- Do not implement face recognition or identity inference.
- Do not claim collision, intent, proximity, direction, or color detection unless a dedicated tested component provides it.
- Do not make legal, insurance, or fault determinations.

## Application conventions
- Streamlit is the user interface.
- OpenCV performs video reading and frame extraction.
- The detector is exposed through an interface so it can be mocked in tests.
- Streamlit session state stores events for the active demo.
- Python dataclasses define application data.
- pytest is used for tests and Ruff for formatting and linting.

## Testing requirements
- Add unit tests for new non-UI behavior.
- Mock object detection in unit tests.
- Use temporary directories in tests.
- Test empty results, invalid videos, unsupported formats, and corrupted input.
- Avoid tests that download model weights or require internet access.

## Privacy and security
- Sanitize filenames and generate internal IDs.
- Restrict allowed file extensions and configurable upload size.
- Keep uploaded content local for the MVP.
- Provide a clear-session action that removes temporary video and thumbnail files.
- Do not log frame contents or personal information.
```

## 12. Copilot implementation prompts

Use these four prompts one at a time. Run the app or tests after each prompt before continuing.

### Prompt 1 — scaffold the repository

```text
Create the small Python 3.11 project structure described in README.md. Use Streamlit, OpenCV, Python dataclasses, pytest, and Ruff. Add pyproject.toml, .gitignore, package files, and a minimal Streamlit app that starts successfully. Do not add a database, API server, cloud service, or object detection yet. Add a smoke test.
```

### Prompt 2 — process video and detect objects

```text
Implement the DetectedEvent dataclass, safe MP4 upload handling, and a VideoProcessor that samples one frame every two seconds without loading the full video into memory. Add an injectable ObjectDetector protocol and a lazy Ultralytics YOLO implementation using yolo11n.pt. Keep only person, bicycle, car, motorcycle, bus, and truck detections. Reject files over 100 MB, videos over two minutes, and unreadable videos with actionable messages. Add focused tests using a fake detector and mocked cv2.VideoCapture; tests must not load model weights.
```

### Prompt 3 — add deterministic search

```text
Implement EventSearchService with a deterministic synonym map: person/people/someone maps to person; car/cars maps to car; vehicle/vehicles maps to bicycle, car, motorcycle, bus, and truck. Sort matches by timestamp and return an empty list for unsupported queries. Add table-driven tests for supported terms, case and punctuation normalization, empty input, and unsupported queries.
```

### Prompt 4 — wire the demo

```text
Build the Streamlit upload, processing progress, search, and results workflow. Keep events in st.session_state. Each result must show a thumbnail, timestamp, label, and confidence. Display the uploaded video above results and provide a clear-session button that deletes temporary files. Handle invalid uploads, processing failures, no detections, and no matches. Then run ruff check, ruff format --check, and pytest, and fix only issues related to this MVP.
```

## 13. Hackathon build plan

### Milestone 1 — working shell

- Repository structure
- Streamlit starts
- MP4 upload and video preview
- Ruff and pytest run locally

### Milestone 2 — complete happy path

- Upload validation
- Sampled frame extraction
- YOLO integration
- Person and vehicle filtering
- Search, thumbnails, and timestamps

### Milestone 3 — demo hardening

- Test one approved 20–60 second video repeatedly
- Pre-download and pre-warm the YOLO model
- Add error, empty, and clear-session states
- Rehearse the three-minute script
- Freeze features before presentation day

## 14. Suggested task allocation

| Workstream | Tasks |
|---|---|
| Application/UI | Streamlit upload, progress, search, and results views |
| Video/AI | Frame extraction, detector integration, thumbnails |
| Search/quality | Query mapping, tests, error states |
| Demo/story | Approved sample video, README, demo script, submission video |

For a team of two, combine Application/UI with Demo/story and Video/AI with Search/quality. For a solo build, finish each milestone before starting the next.

## 15. GitHub workflow

Use short-lived branches:

```text
main
feature/app-shell
feature/detection-search
feature/demo-polish
```

For every pull request:

- Explain the user-visible change.
- Link it to an MVP task.
- Include test evidence.
- Note limitations and privacy considerations.
- Keep generated videos, frames, thumbnails, and model weights out of the commit.

## 16. Optional GitHub Actions workflow

Ask Copilot:

```text
Create a GitHub Actions workflow that runs on pull requests and pushes to main. Use Python 3.11, install the project with dev dependencies, run ruff check, ruff format --check, and pytest. Cache pip dependencies. Do not download object-detection model weights during CI.
```

## 17. Demo script

1. Introduce the problem: reviewing long dashcam recordings manually is slow.
2. Upload a short sample video.
3. Show processing progress.
4. Search for “show me people.”
5. Show the matching timestamp and thumbnail beside the video.
6. Search for “show all vehicles.”
7. Explain that the MVP processes locally and does not identify people.
8. Close with the extension path: stronger event detection, redaction, and cloud scaling.

### Demo guardrails

- Use the same approved sample video for development and judging.
- Keep a second local backup video with the same detectable object types.
- Start the app and warm the model before presenting.
- Do not depend on internet access during the demo.
- Keep screenshots or a short screen recording as a fallback, but demonstrate the live path first.
- Describe detections as model results, not verified facts.

## 18. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Slow processing | Sample frames and limit demo-video duration |
| False detections | Display confidence and describe results as model detections |
| Large files | Enforce configurable size and duration limits |
| Privacy concerns | Process locally, provide deletion, avoid identity recognition |
| Model-download failures | Download weights before the event and keep a fake detector for tests |
| Demo instability | Use a tested short video and pre-warm the model before presenting |

## 19. Future ideas

After the MVP works end to end:

- Semantic search with embeddings
- Better collision detection using motion and audio signals
- Number-plate and face redaction
- Vehicle direction and proximity estimation
- GPS and map timeline integration
- Automatic incident report generation
- Evidence export with timestamps and checksums
- Azure Blob Storage and queued background processing
- Azure AI Video Indexer evaluation
- Multi-camera support

## 20. First working session checklist

- [ ] Create the GitHub repository.
- [ ] Add this guide as `README.md` or retain it as the project plan.
- [ ] Add `.github/copilot-instructions.md`.
- [ ] Run Copilot Prompt 1 to scaffold the repository.
- [ ] Confirm the Streamlit application starts.
- [ ] Confirm linting and the smoke test pass.
- [ ] Assign owners for UI, video/AI, data/search, and demo quality.
- [ ] Select one short, approved sample video.
- [ ] Create GitHub issues for Milestones 1–3.
- [ ] Complete the deterministic workflow before attempting any stretch goal.
- [ ] Rehearse the live demo twice on the presentation machine.
