$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "Virtual environment not found. Run .\scripts\setup.ps1 first."
}

Push-Location $ProjectRoot
try {
    Remove-Item dist -Recurse -Force -ErrorAction SilentlyContinue
    & $Python -m build
    Write-Host "Packages created in .\dist"
}
finally {
    Pop-Location
}
