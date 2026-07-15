$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root "venv\Scripts\python.exe"
$Targets = @("src", "tests/domain", "tests/configuration", "tests/regulatory", "tests/data", "tests/models", "tests/application", "tests/validation", "tests/infrastructure/test_database.py", "tests/interfaces", "tests/security", "tests/audit", "scripts/bootstrap_api_user.py", "scripts/generate_pd_backtest_report.py", "scripts/generate_lgd_backtest_report.py", "scripts/generate_ead_backtest_report.py", "scripts/generate_ecl_backtest_report.py")

Push-Location $Root
try {
    & $Python -m black --check @Targets
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $Python -m ruff check @Targets
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $Python -m mypy src/domain src/data/synthetic src/models/pd src/models/sicr src/models/lgd src/models/ead src/models/forward_looking src/ecl/calculation src/ecl/discounting src/ecl/overlays src/ecl/stage3 src/agent src/application/services src/infrastructure/configuration src/infrastructure/database src/interfaces/api src/security src/audit src/regulatory/cmn4966 src/regulatory/traceability src/validation/backtesting src/validation/model_risk src/validation/reconciliation scripts/bootstrap_api_user.py scripts/generate_pd_backtest_report.py scripts/generate_lgd_backtest_report.py scripts/generate_ead_backtest_report.py scripts/generate_ecl_backtest_report.py
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $Python -m pytest tests/domain tests/configuration tests/regulatory tests/data tests/models tests/application tests/validation tests/infrastructure/test_database.py tests/interfaces tests/security tests/audit --cov=src --cov-report=term-missing
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $Python -m pytest backend/bancos_de_dados/tests backend/prinad/tests -q
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Push-Location (Join-Path $Root "frontend")
    try {
        npm run build
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
    finally {
        Pop-Location
    }
}
finally {
    Pop-Location
}
