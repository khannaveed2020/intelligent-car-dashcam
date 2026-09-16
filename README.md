# Intelligent Car Dashcam

A local hackathon MVP that finds people and vehicles in short dashcam videos. Upload an MP4, process sampled frames with YOLO, and search the results using phrases such as "show me people" or "show all vehicles."

## Fastest setup

Requirements: Python 3.11 or later and internet access during setup. Setup downloads the small YOLO model once so the presentation can run offline.

### Windows PowerShell

```powershell
.\scripts\setup.ps1
.\scripts\run.ps1
```

### macOS or Linux

```bash
chmod +x scripts/setup.sh scripts/run.sh
./scripts/setup.sh
./scripts/run.sh
```

Open <http://localhost:8501>, upload an MP4 under 100 MB and two minutes, then select **Process video**.

## Docker

Docker packages Python, system libraries, dependencies, and the model in one image:

```bash
docker compose up --build
```

The first image build requires internet access. Later starts can run offline with `docker compose up`. Stop with `docker compose down`; add `-v` to remove the local RoadLens data volume.

## Installable package

Build a wheel and source archive on Windows:

```powershell
.\scripts\setup.ps1 -SkipModel
.\scripts\build-package.ps1
```

Install a release wheel on another computer:

```bash
python -m venv .venv
# Windows: .venv\Scripts\python -m pip install intelligent_car_dashcam-0.1.0-py3-none-any.whl
# macOS/Linux: .venv/bin/python -m pip install intelligent_car_dashcam-0.1.0-py3-none-any.whl
roadlens
```

The wheel intentionally excludes model weights and videos. The model downloads to the writable per-user cache on first use unless native setup prewarmed it or the Docker image included it. Set `ROADLENS_DATA_DIR` or `ROADLENS_MODEL_PATH` to override those locations.

## Validate

```powershell
ruff check .
ruff format --check .
pytest
```

## Demo queries

- `Show me people`
- `Find the cars`
- `Show all vehicles`

## Presentation checklist

- Use a tested 20–60 second H.264 MP4 containing at least one person and one vehicle.
- Transfer the approved demo video separately; video files are intentionally excluded from Git and packages.
- Complete setup while online, then start RoadLens once before going offline.
- Keep a second approved clip and a short screen recording as fallbacks.
- Run `pytest`, `ruff check .`, and `ruff format --check .` before presenting.

## Privacy and limitations

Videos and thumbnails remain on the local machine and can be removed with **Clear session**. Results are model detections, not verified facts. This MVP does not perform face recognition, identity inference, collision detection, color classification, or legal analysis.

See [intelligent_car_dashcam_mvp_copilot_guide.md](intelligent_car_dashcam_mvp_copilot_guide.md) for the project plan and demo script.
