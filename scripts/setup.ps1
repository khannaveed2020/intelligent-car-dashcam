param(
    [switch]$SkipModel
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VirtualEnvironment = Join-Path $ProjectRoot ".venv"
$Python = Join-Path $VirtualEnvironment "Scripts\python.exe"

Push-Location $ProjectRoot
try {
    if (-not (Test-Path $Python)) {
        python -m venv $VirtualEnvironment
    }

    & $Python -m pip install --upgrade pip
    & $Python -m pip install -e ".[dev]"

    if (-not $SkipModel) {
        & $Python -c "from app.detector import YoloObjectDetector; YoloObjectDetector().load(); print('YOLO model ready')"
    }

    Write-Host "RoadLens setup complete. Run: .\scripts\run.ps1"
}
finally {
    Pop-Location
}
