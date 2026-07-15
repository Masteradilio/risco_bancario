"""Generate the versioned synthetic PD backtest evidence package."""

from __future__ import annotations

import json
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path

import numpy as np

from src.data.synthetic import (
    PopulationConfig,
    build_modeling_datasets,
    generate_credit_events,
    generate_macroeconomic_bundle,
    generate_monthly_history,
    generate_population,
)
from src.data.synthetic.modeling import PDModelingRow
from src.models.pd.baselines import _frame
from src.models.pd.calibration import calibrate_explainable_pd
from src.validation.backtesting import (
    PDBacktestObservation,
    backtest_pd,
    render_pd_backtest_report,
)

OUTPUT_DIRECTORY = Path("evidence/validation/pd/2026.07.1")


def _one_month_probability(twelve_month_probability: float) -> Decimal:
    probability = 1 - (1 - twelve_month_probability) ** (1 / 12)
    return Decimal(str(probability))


def _observations(
    rows: list[PDModelingRow], predictions: np.ndarray, split: str
) -> tuple[PDBacktestObservation, ...]:
    result: list[PDBacktestObservation] = []
    for row, prediction in zip(rows, predictions, strict=True):
        targets = {1: row.target_hazard_1m, 12: row.target_default_12m}
        probabilities = {
            1: _one_month_probability(float(prediction)),
            12: Decimal(str(float(prediction))),
        }
        for horizon in (1, 12):
            target = targets[horizon]
            if target is None:
                raise ValueError(f"immature target in {split}: {row.contract_id}")
            result.append(
                PDBacktestObservation(
                    f"{row.observation_date.isoformat()}:{row.contract_id}:{horizon}",
                    row.observation_date,
                    horizon,
                    probabilities[horizon],
                    target,
                    row.rating,
                    row.product_code,
                    row.origination_cohort[:4],
                    split,
                )
            )
    return tuple(result)


def main() -> None:
    population = generate_population(PopulationConfig(seed=91, clients=40, contracts_per_client=2))
    history = generate_monthly_history(population)
    events = generate_credit_events(population, history)
    modeling = build_modeling_datasets(
        population,
        history,
        events,
        generate_macroeconomic_bundle(91),
    )
    calibration = calibrate_explainable_pd(modeling)
    reference_rows = [item for item in modeling.pd if item.split == "calibration"]
    evaluation_rows = [item for item in modeling.pd if item.split == "oot"]
    future_rows = [item for item in modeling.pd if item.split == "backtesting"]
    reference_predictions = calibration.calibrated_pipeline.predict_proba(_frame(reference_rows))[
        :, 1
    ]
    evaluation_predictions = calibration.calibrated_pipeline.predict_proba(_frame(evaluation_rows))[
        :, 1
    ]
    report = backtest_pd(
        "logistic_12m_isotonic_frozen",
        "synthetic-2026.07.1",
        _observations(reference_rows, reference_predictions, "calibration"),
        _observations(evaluation_rows, evaluation_predictions, "oot"),
        unlabeled_future_observations=len(future_rows),
    )
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIRECTORY / "report.json").write_text(
        json.dumps(asdict(report), sort_keys=True, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    (OUTPUT_DIRECTORY / "report.md").write_text(render_pd_backtest_report(report), encoding="utf-8")


if __name__ == "__main__":
    main()
