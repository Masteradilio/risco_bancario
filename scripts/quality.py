"""Cross-platform quality gate used locally and by continuous integration."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FORMAT_TARGETS = (
    "src",
    "tests/domain",
    "tests/configuration",
    "tests/regulatory",
    "tests/data",
    "tests/models",
    "tests/performance",
    "tests/application",
    "tests/validation",
    "tests/infrastructure/test_database.py",
    "tests/infrastructure/test_ci_contract.py",
    "tests/infrastructure/test_deployment.py",
    "tests/infrastructure/test_observability.py",
    "tests/infrastructure/test_quality_pipeline.py",
    "tests/interfaces",
    "tests/security",
    "tests/audit",
    "scripts/bootstrap_api_user.py",
    "scripts/generate_pd_backtest_report.py",
    "scripts/generate_lgd_backtest_report.py",
    "scripts/generate_ead_backtest_report.py",
    "scripts/generate_ecl_backtest_report.py",
    "scripts/deploy.py",
    "scripts/performance_benchmark.py",
    "scripts/security_maintenance.py",
    "scripts/e2e_pipeline.py",
    "scripts/quality.py",
)

MYPY_TARGETS = (
    "src/domain",
    "src/data/synthetic",
    "src/models/pd",
    "src/models/sicr",
    "src/models/lgd",
    "src/models/ead",
    "src/models/forward_looking",
    "src/ecl/calculation",
    "src/ecl/batch",
    "src/ecl/discounting",
    "src/ecl/overlays",
    "src/ecl/stage3",
    "src/agent",
    "src/application/services",
    "src/application/e2e.py",
    "src/infrastructure/configuration",
    "src/infrastructure/database",
    "src/infrastructure/deployment",
    "src/infrastructure/logging",
    "src/infrastructure/observability",
    "src/interfaces/api",
    "src/security",
    "src/audit",
    "src/regulatory/cmn4966",
    "src/regulatory/traceability",
    "src/validation/backtesting",
    "src/validation/model_risk",
    "src/validation/reconciliation",
    "src/validation/golden_cases.py",
    "scripts/bootstrap_api_user.py",
    "scripts/generate_pd_backtest_report.py",
    "scripts/generate_lgd_backtest_report.py",
    "scripts/generate_ead_backtest_report.py",
    "scripts/generate_ecl_backtest_report.py",
    "scripts/deploy.py",
    "scripts/performance_benchmark.py",
    "scripts/security_maintenance.py",
    "scripts/e2e_pipeline.py",
    "scripts/quality.py",
)

TEST_TARGETS = (
    "tests/domain",
    "tests/configuration",
    "tests/regulatory",
    "tests/data",
    "tests/models",
    "tests/performance",
    "tests/application",
    "tests/validation",
    "tests/infrastructure/test_database.py",
    "tests/infrastructure/test_ci_contract.py",
    "tests/infrastructure/test_deployment.py",
    "tests/infrastructure/test_observability.py",
    "tests/infrastructure/test_quality_pipeline.py",
    "tests/interfaces",
    "tests/security",
    "tests/audit",
)


def command_matrix() -> dict[str, tuple[tuple[str, ...], ...]]:
    """Return the authoritative commands, suitable for contract testing."""
    python = sys.executable
    npm = "npm.cmd" if os.name == "nt" else "npm"
    return {
        "static": (
            (python, "-m", "black", "--check", *FORMAT_TARGETS),
            (python, "-m", "ruff", "check", *FORMAT_TARGETS),
            (python, "-m", "ruff", "check", "src", "--select", "S"),
            (python, "-m", "mypy", *MYPY_TARGETS),
        ),
        "tests": (
            (
                python,
                "-m",
                "pytest",
                *TEST_TARGETS,
                "--cov=src",
                "--cov-report=term-missing",
                "--cov-report=xml",
            ),
            (python, "-m", "pytest", "backend/bancos_de_dados/tests", "backend/prinad/tests", "-q"),
        ),
        "frontend": ((npm, "run", "build"),),
    }


def run(stage: str) -> None:
    stages = tuple(command_matrix()) if stage == "all" else (stage,)
    for selected in stages:
        cwd = ROOT / "frontend" if selected == "frontend" else ROOT
        for command in command_matrix()[selected]:
            print(f"[quality:{selected}] {' '.join(command)}", flush=True)
            subprocess.run(command, cwd=cwd, check=True)  # noqa: S603


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage",
        choices=("all", "static", "tests", "frontend"),
        default="all",
        help="Gate section to execute (default: all).",
    )
    run(parser.parse_args().stage)


if __name__ == "__main__":
    main()
