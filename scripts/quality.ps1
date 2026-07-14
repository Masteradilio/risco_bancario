$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root "venv\Scripts\python.exe"
$Targets = @("src", "tests/domain", "tests/configuration", "tests/regulatory", "tests/data", "tests/models")

Push-Location $Root
try {
    & $Python -m black --check @Targets
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $Python -m ruff check @Targets
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $Python -m mypy src/domain src/data/synthetic src/models/pd src/models/sicr src/ecl/calculation src/infrastructure/configuration src/regulatory/traceability
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $Python -m pytest tests/domain tests/configuration tests/regulatory tests/data tests/models --cov=src --cov-report=term-missing
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $Python -m pytest backend/bancos_de_dados/tests backend/prinad/tests -q
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
finally {
    Pop-Location
}
