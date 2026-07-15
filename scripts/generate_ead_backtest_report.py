"""Generate the versioned synthetic EAD/CCF backtest evidence package."""

from __future__ import annotations

import json
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path

from src.data.synthetic import (
    PopulationConfig,
    generate_credit_events,
    generate_monthly_history,
    generate_population,
)
from src.models.ead import (
    build_amortized_default_ead_dataset,
    build_revolving_ccf_dataset,
    fit_revolving_ccf_model,
    load_amortized_ead_policy,
    load_revolving_ccf_policy,
    predict_revolving_ccf,
)
from src.validation.backtesting import (
    EADBacktestObservation,
    backtest_ead,
    render_ead_backtest_report,
)

OUTPUT_DIRECTORY = Path("evidence/validation/ead/2026.07.1")


def _utilization_band(value: Decimal) -> str:
    if value < Decimal("0.33"):
        return "low"
    if value < Decimal("0.66"):
        return "medium"
    return "high"


def main() -> None:
    ccf_policy = load_revolving_ccf_policy(Path("config/ccf_policy/2026.07.1.json"))
    development = generate_population(
        PopulationConfig(
            seed=ccf_policy.development_seed,
            clients=ccf_policy.development_clients,
            contracts_per_client=ccf_policy.development_contracts_per_client,
        )
    )
    development_history = generate_monthly_history(development)
    development_events = generate_credit_events(development, development_history)
    ccf_dataset = build_revolving_ccf_dataset(
        development, development_history, development_events, ccf_policy
    )
    ccf_model = fit_revolving_ccf_model(ccf_dataset)
    ccf_rows = tuple(
        item
        for item in ccf_dataset.rows
        if item.split == "validation" and item.target_ccf is not None
    )
    ccf_predictions = predict_revolving_ccf(ccf_model, ccf_rows)

    acceptance = generate_population(PopulationConfig(seed=91, clients=40, contracts_per_client=2))
    acceptance_history = generate_monthly_history(acceptance)
    acceptance_events = generate_credit_events(acceptance, acceptance_history)
    amortized = build_amortized_default_ead_dataset(
        acceptance,
        acceptance_history,
        acceptance_events,
        load_amortized_ead_policy(Path("config/ead_policy/2026.07.1.json")),
    )

    observations = [
        EADBacktestObservation(
            item.default_id,
            "amortized",
            item.product_code,
            item.projected_ead,
            item.observed_ead,
            "not_applicable",
        )
        for item in amortized.records
    ]
    for row, prediction in zip(ccf_rows, ccf_predictions, strict=True):
        predicted_ccf = Decimal(str(prediction))
        actual_ccf = row.target_ccf
        if actual_ccf is None:
            raise ValueError("validation CCF target unexpectedly absent")
        observations.append(
            EADBacktestObservation(
                f"{row.default_id}:{row.horizon_months}m",
                "revolving",
                row.product_code,
                row.observed_balance + row.available_limit * predicted_ccf,
                row.ead_at_default,
                _utilization_band(row.utilization),
                predicted_ccf,
                actual_ccf,
            )
        )
    report = backtest_ead(
        "ead_amortized_and_revolving_ccf",
        "synthetic-2026.07.1",
        tuple(observations),
    )
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIRECTORY / "report.json").write_text(
        json.dumps(asdict(report), sort_keys=True, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    (OUTPUT_DIRECTORY / "report.md").write_text(
        render_ead_backtest_report(report), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
