param(
    [string]$Output = "data/synthetic/acceptance-v0.1.0",
    [int]$Seed = 91,
    [int]$Clients = 40,
    [int]$ContractsPerClient = 2
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $RepoRoot "venv/Scripts/python.exe"

if (-not (Test-Path $Python)) {
    throw "Project venv not found at $Python. Run scripts/setup.ps1 first."
}

& $Python -m src.data.synthetic.export `
    --output (Join-Path $RepoRoot $Output) `
    --seed $Seed `
    --clients $Clients `
    --contracts-per-client $ContractsPerClient
