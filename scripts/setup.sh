#!/usr/bin/env sh
set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$PROJECT_ROOT"

PYTHON=${PYTHON:-python3}
"$PYTHON" -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e ".[dev]"

if [ "${SKIP_MODEL:-0}" != "1" ]; then
    .venv/bin/python -c "from app.detector import YoloObjectDetector; YoloObjectDetector().load(); print('YOLO model ready')"
fi

printf '%s\n' "RoadLens setup complete. Run: ./scripts/run.sh"
