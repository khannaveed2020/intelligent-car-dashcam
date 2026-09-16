$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$RoadLens = Join-Path $ProjectRoot ".venv\Scripts\roadlens.exe"

if (-not (Test-Path $RoadLens)) {
    throw "RoadLens is not installed. Run .\scripts\setup.ps1 first."
}

Push-Location $ProjectRoot
try {
    & $RoadLens @args
}
finally {
    Pop-Location
}
