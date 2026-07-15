"""Generate the versioned synthetic ECL backtest evidence package."""

from __future__ import annotations

import json
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path

from src.data.synthetic import (
    PopulationConfig,
    generate_population,
)
from src.validation.backtesting import (
    ECLBacktestObservation,
    backtest_ecl,
    render_ecl_backtest_report,
)

OUTPUT_DIRECTORY = Path("evidence/validation/ecl/2026.07.1")


def main() -> None:
    population = generate_population(PopulationConfig(seed=91, clients=40, contracts_per_client=2))
    observations = [
        ECLBacktestObservation(
            observation_id=contract.contract_id,
            initial_ecl=Decimal("0.00"),
            realized_loss=None,
            vintage=str(contract.origination_date.year),
            economic_cycle="normal",
            attribution_path=None,
        )
        for contract in population.contracts
    ]
    report = backtest_ecl(
        "probability_weighted_ecl",
        "synthetic-2026.07.1",
        tuple(observations),
    )
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIRECTORY / "report.json").write_text(
        json.dumps(asdict(report), sort_keys=True, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    (OUTPUT_DIRECTORY / "report.md").write_text(
        render_ecl_backtest_report(report), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
