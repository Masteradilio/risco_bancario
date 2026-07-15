"""Generate the versioned synthetic LGD backtest evidence package."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date
from decimal import Decimal
from pathlib import Path

from src.data.synthetic import (
    PopulationConfig,
    generate_credit_events,
    generate_macroeconomic_bundle,
    generate_monthly_history,
    generate_population,
)
from src.models.lgd import (
    build_lgd_modeling_dataset,
    build_lgd_workout_dataset,
    calculate_realized_lgd_dataset,
    fit_lgd_models,
    load_lgd_validation_policy,
    load_realized_lgd_policy,
    validate_lgd_model,
)
from src.validation.backtesting import (
    LGDBacktestObservation,
    backtest_lgd,
    render_lgd_backtest_report,
)

OUTPUT_DIRECTORY = Path("evidence/validation/lgd/2026.07.1")


def main() -> None:
    population = generate_population(PopulationConfig(seed=91, clients=40, contracts_per_client=2))
    history = generate_monthly_history(population)
    events = generate_credit_events(population, history)
    workout = build_lgd_workout_dataset(population, events, observation_end_date=date(2025, 12, 1))
    realized = calculate_realized_lgd_dataset(
        workout, load_realized_lgd_policy(Path("config/lgd_policy/2026.07.1.json"))
    )
    dataset = build_lgd_modeling_dataset(
        workout,
        realized,
        population,
        history,
        generate_macroeconomic_bundle(seed=91),
    )
    comparison = fit_lgd_models(dataset)
    development_report = validate_lgd_model(
        dataset,
        comparison,
        load_lgd_validation_policy(Path("config/lgd_validation/2026.07.1.json")),
    )
    workout_by_id = {item.default_id: item for item in workout.records}
    realized_by_id = {item.default_id: item for item in realized}
    observations: list[LGDBacktestObservation] = []
    for prediction in development_report.predictions:
        source = workout_by_id[prediction.default_id]
        outcome = realized_by_id[prediction.default_id]
        observations.append(
            LGDBacktestObservation(
                source.default_id,
                source.default_cohort,
                source.product_code,
                source.exposure_at_default,
                Decimal(str(prediction.predicted_lgd)),
                outcome.realized_lgd,
                outcome.discounted_net_recoveries,
                "closed",
                source.cure_date is not None,
                source.writeoff_amount,
                source.collateral_type is not None,
            )
        )
    for source in workout.records:
        if not source.is_censored:
            continue
        outcome = realized_by_id[source.default_id]
        observations.append(
            LGDBacktestObservation(
                source.default_id,
                source.default_cohort,
                source.product_code,
                source.exposure_at_default,
                None,
                None,
                outcome.discounted_net_recoveries,
                "open",
                source.cure_date is not None,
                source.writeoff_amount,
                source.collateral_type is not None,
            )
        )
    report = backtest_lgd(
        development_report.model_name,
        "synthetic-2026.07.1",
        tuple(observations),
    )
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIRECTORY / "report.json").write_text(
        json.dumps(asdict(report), sort_keys=True, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    (OUTPUT_DIRECTORY / "report.md").write_text(
        render_lgd_backtest_report(report), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
