"""Integrity, temporal and leakage diagnostics for synthetic datasets."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from statistics import fmean

from .events import CreditEventHistory
from .longitudinal import LongitudinalPortfolio
from .macroeconomics import MacroeconomicBundle
from .modeling import MAX_LABELED_OBSERVATION_DATE, MAX_OBSERVATION_DATE, ModelingDatasets
from .population import SyntheticPortfolio

PD_FEATURE_COLUMNS = (
    "balance",
    "credit_limit",
    "utilization",
    "days_past_due",
    "behavior_score",
    "gdp_growth",
    "inflation",
    "policy_rate",
    "unemployment",
    "household_debt",
)
FORBIDDEN_FEATURE_TOKENS = (
    "_latent",
    "target_",
    "future",
    "default_date",
    "recovery",
    "writeoff",
    "write_off",
    "exposure_at_default",
)


@dataclass(frozen=True, slots=True)
class QualityIssue:
    code: str
    table: str
    detail: str


@dataclass(frozen=True, slots=True)
class DistributionSummary:
    column: str
    count: int
    minimum: float
    maximum: float
    mean: float


@dataclass(frozen=True, slots=True)
class CorrelationSummary:
    feature: str
    target: str
    pearson: float


@dataclass(frozen=True, slots=True)
class SyntheticQualityReport:
    issues: tuple[QualityIssue, ...]
    distributions: tuple[DistributionSummary, ...]
    correlations: tuple[CorrelationSummary, ...]

    @property
    def passed(self) -> bool:
        return not self.issues


def detect_future_features(columns: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    return tuple(
        column
        for column in columns
        if any(token in column.lower() for token in FORBIDDEN_FEATURE_TOKENS)
    )


def _pearson(left: list[float], right: list[float]) -> float:
    left_mean = fmean(left)
    right_mean = fmean(right)
    numerator = sum(
        (left_item - left_mean) * (right_item - right_mean)
        for left_item, right_item in zip(left, right, strict=True)
    )
    left_scale = sqrt(sum((item - left_mean) ** 2 for item in left))
    right_scale = sqrt(sum((item - right_mean) ** 2 for item in right))
    if left_scale == 0 or right_scale == 0:
        return 0.0
    return numerator / (left_scale * right_scale)


def _referential_issues(
    population: SyntheticPortfolio,
    history: LongitudinalPortfolio,
    events: CreditEventHistory,
) -> list[QualityIssue]:
    issues: list[QualityIssue] = []
    contract_ids = {item.contract_id for item in population.contracts}
    client_ids = {item.client_id for item in population.clients}
    default_ids = {item.default_id for item in events.defaults}
    for snapshot in history.snapshots:
        if snapshot.contract_id not in contract_ids or snapshot.client_id not in client_ids:
            issues.append(
                QualityIssue("orphan_snapshot", "monthly_snapshots", snapshot.contract_id)
            )
    for default in events.defaults:
        if default.contract_id not in contract_ids:
            issues.append(QualityIssue("orphan_default", "defaults", default.default_id))
    for table_name, rows in (
        ("collections", events.collections),
        ("recoveries", events.recoveries),
        ("cures", events.cures),
        ("writeoffs", events.writeoffs),
    ):
        for row in rows:
            if row.default_id not in default_ids:
                issues.append(QualityIssue("orphan_default_reference", table_name, row.default_id))
    return issues


def _temporal_issues(
    history: LongitudinalPortfolio,
    events: CreditEventHistory,
    modeling: ModelingDatasets,
) -> list[QualityIssue]:
    issues: list[QualityIssue] = []
    seen_snapshots: set[tuple[str, object]] = set()
    for snapshot in history.snapshots:
        key = (snapshot.contract_id, snapshot.reference_date)
        if key in seen_snapshots:
            issues.append(QualityIssue("duplicate_snapshot", "monthly_snapshots", str(key)))
        seen_snapshots.add(key)
    defaults = {item.default_id: item for item in events.defaults}
    for recovery in events.recoveries:
        default = defaults.get(recovery.default_id)
        if default is not None and recovery.recovery_date <= default.default_date:
            issues.append(
                QualityIssue("recovery_before_default", "recoveries", recovery.recovery_id)
            )
        if recovery.net_amount != recovery.gross_amount - recovery.cost_amount:
            issues.append(
                QualityIssue("recovery_not_reconciled", "recoveries", recovery.recovery_id)
            )
    for cure in events.cures:
        default = defaults.get(cure.default_id)
        if default is not None and cure.cure_date <= default.default_date:
            issues.append(QualityIssue("cure_before_default", "cures", cure.cure_id))
    if any(item.observation_date > MAX_OBSERVATION_DATE for item in modeling.pd):
        issues.append(QualityIssue("observation_after_cutoff", "pd_modeling", "after 2025-12-01"))
    if any(
        item.observation_date <= MAX_LABELED_OBSERVATION_DATE
        and (item.target_default_12m is None or item.target_hazard_1m is None)
        for item in modeling.pd
    ):
        issues.append(QualityIssue("missing_mature_target", "pd_modeling", "through 2024-12-01"))
    if any(
        item.observation_date > MAX_LABELED_OBSERVATION_DATE
        and (item.target_default_12m is not None or item.target_hazard_1m is not None)
        for item in modeling.pd
    ):
        issues.append(QualityIssue("premature_future_target", "pd_modeling", "after 2024-12-01"))
    return issues


def assess_synthetic_quality(
    population: SyntheticPortfolio,
    history: LongitudinalPortfolio,
    events: CreditEventHistory,
    macro: MacroeconomicBundle,
    modeling: ModelingDatasets,
) -> SyntheticQualityReport:
    issues = _referential_issues(population, history, events)
    issues.extend(_temporal_issues(history, events, modeling))
    leaks = detect_future_features(list(PD_FEATURE_COLUMNS))
    issues.extend(QualityIssue("future_feature", "pd_modeling", item) for item in leaks)
    if len(macro.observed) != 120:
        issues.append(
            QualityIssue("macro_history_incomplete", "macro_observed", str(len(macro.observed)))
        )
    required_splits = {"train", "validation", "calibration", "oot", "backtesting"}
    observed_splits = {item.split for item in modeling.pd}
    if observed_splits != required_splits:
        issues.append(QualityIssue("missing_time_split", "pd_modeling", str(observed_splits)))

    labeled_pd = [item for item in modeling.pd if item.target_default_12m is not None]
    targets = [float(item.target_default_12m == 1) for item in labeled_pd]
    distributions: list[DistributionSummary] = []
    correlations: list[CorrelationSummary] = []
    for feature in PD_FEATURE_COLUMNS:
        values = [float(getattr(item, feature)) for item in modeling.pd]
        labeled_values = [float(getattr(item, feature)) for item in labeled_pd]
        distributions.append(
            DistributionSummary(feature, len(values), min(values), max(values), fmean(values))
        )
        correlations.append(
            CorrelationSummary(feature, "target_default_12m", _pearson(labeled_values, targets))
        )
    return SyntheticQualityReport(tuple(issues), tuple(distributions), tuple(correlations))
