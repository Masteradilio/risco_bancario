$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root "venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $Python)) {
    py -3.13 -m venv (Join-Path $Root "venv")
}

& $Python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $Python -m pip install -e "$Root[dev]"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $Python -c "from src.domain.contracts import Contract; print('setup ok')"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
