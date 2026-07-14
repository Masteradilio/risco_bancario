$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root "venv\Scripts\python.exe"

Push-Location $Root
try {
    & $Python -m src.regulatory.traceability.report @args
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
