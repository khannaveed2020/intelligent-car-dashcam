#!/usr/bin/env sh
set -eu

PROJECT_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
ROADLENS="$PROJECT_ROOT/.venv/bin/roadlens"

if [ ! -x "$ROADLENS" ]; then
    printf '%s\n' "RoadLens is not installed. Run ./scripts/setup.sh first." >&2
    exit 1
fi

cd "$PROJECT_ROOT"
exec "$ROADLENS" "$@"
