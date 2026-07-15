$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root "venv\Scripts\python.exe"
$Targets = @("src", "tests/domain", "tests/configuration", "tests/regulatory", "tests/data", "tests/models", "tests/application", "tests/validation", "scripts/generate_pd_backtest_report.py", "scripts/generate_lgd_backtest_report.py")

Push-Location $Root
try {
    & $Python -m black --check @Targets
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $Python -m ruff check @Targets
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $Python -m mypy src/domain src/data/synthetic src/models/pd src/models/sicr src/models/lgd src/models/ead src/models/forward_looking src/ecl/calculation src/ecl/discounting src/ecl/overlays src/ecl/stage3 src/application/services src/infrastructure/configuration src/regulatory/cmn4966 src/regulatory/traceability src/validation/backtesting src/validation/model_risk src/validation/reconciliation scripts/generate_pd_backtest_report.py scripts/generate_lgd_backtest_report.py
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $Python -m pytest tests/domain tests/configuration tests/regulatory tests/data tests/models tests/application tests/validation --cov=src --cov-report=term-missing
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $Python -m pytest backend/bancos_de_dados/tests backend/prinad/tests -q
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
finally {
    Pop-Location
}
