"""Synthetic staging validation for relative and absolute SICR definitions."""

from __future__ import annotations

from dataclasses import dataclass
from math import log

from ...data.synthetic.modeling import ModelingDatasets, SICRModelingRow

RATING_ORDER = ("A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2", "C3", "D", "DEFAULT")


@dataclass(frozen=True, slots=True)
class SICRConfusion:
    true_positive: int
    false_positive: int
    true_negative: int
    false_negative: int
    precision: float
    recall: float
    false_positive_rate: float
    false_negative_rate: float


@dataclass(frozen=True, slots=True)
class StabilityPeriod:
    period: str
    row_count: int
    stage2_rate: float
    population_stability_index: float


@dataclass(frozen=True, slots=True)
class StageMigration:
    from_stage: int
    to_stage: int
    count: int
    rate_from_origin: float


@dataclass(frozen=True, slots=True)
class ThresholdSensitivity:
    downgrade_notches: int
    days_past_due: int
    predicted_stage2_rate: float
    confusion: SICRConfusion


@dataclass(frozen=True, slots=True)
class DefinitionComparison:
    relative_confusion: SICRConfusion
    absolute_confusion: SICRConfusion
    agreement_rate: float


@dataclass(frozen=True, slots=True)
class SICRValidationReport:
    evaluation_split: str
    sample_count: int
    event_count: int
    stability: tuple[StabilityPeriod, ...]
    migrations: tuple[StageMigration, ...]
    sensitivity: tuple[ThresholdSensitivity, ...]
    definition_comparison: DefinitionComparison
    false_positive_contracts: tuple[str, ...]
    false_negative_contracts: tuple[str, ...]
    evidence_scope: str
    approval_status: str


def _notches(row: SICRModelingRow) -> int:
    return max(
        0, RATING_ORDER.index(row.current_rating) - RATING_ORDER.index(row.origination_rating)
    )


def _relative(row: SICRModelingRow, downgrade: int = 2, dpd: int = 31) -> bool:
    return row.days_past_due >= dpd or _notches(row) >= downgrade


def _absolute(row: SICRModelingRow) -> bool:
    return row.days_past_due >= 31 or RATING_ORDER.index(row.current_rating) >= RATING_ORDER.index(
        "B1"
    )


def _confusion(target: list[bool], prediction: list[bool]) -> SICRConfusion:
    tp = sum(expected and actual for expected, actual in zip(target, prediction, strict=True))
    fp = sum(not expected and actual for expected, actual in zip(target, prediction, strict=True))
    tn = sum(
        not expected and not actual for expected, actual in zip(target, prediction, strict=True)
    )
    fn = sum(expected and not actual for expected, actual in zip(target, prediction, strict=True))
    return SICRConfusion(
        tp,
        fp,
        tn,
        fn,
        tp / (tp + fp) if tp + fp else 0.0,
        tp / (tp + fn) if tp + fn else 0.0,
        fp / (fp + tn) if fp + tn else 0.0,
        fn / (fn + tp) if fn + tp else 0.0,
    )


def _binary_psi(reference_rate: float, comparison_rate: float) -> float:
    epsilon = 1e-6
    ref = (max(reference_rate, epsilon), max(1 - reference_rate, epsilon))
    comp = (max(comparison_rate, epsilon), max(1 - comparison_rate, epsilon))
    return sum(
        (current - prior) * log(current / prior) for prior, current in zip(ref, comp, strict=True)
    )


def _stability(rows: list[SICRModelingRow]) -> tuple[StabilityPeriod, ...]:
    periods = ("train", "validation", "calibration", "oot")
    rates: dict[str, tuple[int, float]] = {}
    for period in periods:
        group = [item for item in rows if item.split == period]
        rates[period] = (len(group), sum(_relative(item) for item in group) / len(group))
    reference = rates["train"][1]
    return tuple(
        StabilityPeriod(period, count, rate, _binary_psi(reference, rate))
        for period, (count, rate) in rates.items()
    )


def _migrations(rows: list[SICRModelingRow]) -> tuple[StageMigration, ...]:
    by_contract: dict[str, list[SICRModelingRow]] = {}
    for item in rows:
        by_contract.setdefault(item.contract_id, []).append(item)
    counts: dict[tuple[int, int], int] = {}
    origin_totals: dict[int, int] = {}
    for contract_rows in by_contract.values():
        contract_rows.sort(key=lambda item: item.observation_date)
        stages = [2 if _relative(item) else 1 for item in contract_rows]
        for origin, destination in zip(stages[:-1], stages[1:], strict=True):
            counts[(origin, destination)] = counts.get((origin, destination), 0) + 1
            origin_totals[origin] = origin_totals.get(origin, 0) + 1
    return tuple(
        StageMigration(origin, destination, count, count / origin_totals[origin])
        for (origin, destination), count in sorted(counts.items())
    )


def validate_sicr_staging(modeling: ModelingDatasets) -> SICRValidationReport:
    mature = [item for item in modeling.sicr if item.target_sicr_12m is not None]
    oot = [item for item in mature if item.split == "oot"]
    target = [item.target_sicr_12m == 1 for item in oot]
    relative = [_relative(item) for item in oot]
    absolute = [_absolute(item) for item in oot]
    settings = {(1, 31), (2, 31), (3, 31), (2, 15), (2, 60)}
    sensitivity: list[ThresholdSensitivity] = []
    for downgrade, dpd in sorted(settings):
        prediction = [_relative(item, downgrade, dpd) for item in oot]
        sensitivity.append(
            ThresholdSensitivity(
                downgrade,
                dpd,
                sum(prediction) / len(prediction),
                _confusion(target, prediction),
            )
        )
    relative_confusion = _confusion(target, relative)
    comparison = DefinitionComparison(
        relative_confusion,
        _confusion(target, absolute),
        sum(left == right for left, right in zip(relative, absolute, strict=True)) / len(oot),
    )
    false_positive = tuple(
        sorted(
            {
                item.contract_id
                for item, expected, actual in zip(oot, target, relative, strict=True)
                if actual and not expected
            }
        )
    )
    false_negative = tuple(
        sorted(
            {
                item.contract_id
                for item, expected, actual in zip(oot, target, relative, strict=True)
                if expected and not actual
            }
        )
    )
    return SICRValidationReport(
        "oot",
        len(oot),
        sum(target),
        _stability(mature),
        _migrations(oot),
        tuple(sensitivity),
        comparison,
        false_positive,
        false_negative,
        "synthetic_proxy_without_approved_pd",
        "not_approved",
    )
