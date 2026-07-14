"""Realized and modeled CCF for revolving facilities."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal
from hashlib import sha256
from math import sqrt
from pathlib import Path
from typing import Any, cast

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
from sklearn.compose import ColumnTransformer  # type: ignore[import-untyped]
from sklearn.linear_model import Ridge  # type: ignore[import-untyped]
from sklearn.pipeline import Pipeline  # type: ignore[import-untyped]
from sklearn.preprocessing import OneHotEncoder, StandardScaler  # type: ignore[import-untyped]

from ...data.synthetic.events import CreditEventHistory
from ...data.synthetic.longitudinal import LongitudinalPortfolio, MonthlySnapshotRecord
from ...data.synthetic.population import SyntheticPortfolio, _add_months
from ...domain.exceptions import DomainValidationError

QUANTUM = Decimal("0.00000001")
NUMERIC_FEATURES = ("utilization", "horizon_months", "utilization_horizon_interaction")
CATEGORICAL_FEATURES = ("product_code", "limit_status")


@dataclass(frozen=True, slots=True)
class RevolvingCCFPolicy:
    policy_version: str
    effective_from: date
    evidence_status: str
    horizons_months: tuple[int, ...]
    lower_bound: Decimal
    upper_bound: Decimal
    zero_available_limit_treatment: str
    out_of_bounds_treatment: str
    development_seed: int
    development_clients: int
    development_contracts_per_client: int
    sha256: str


@dataclass(frozen=True, slots=True)
class RealizedCCF:
    observed_balance: Decimal
    observed_limit: Decimal
    available_limit: Decimal
    limit_at_default: Decimal
    ead_at_default: Decimal
    incremental_drawdown: Decimal
    raw_ccf: Decimal | None
    realized_ccf: Decimal | None
    ccf_defined: bool
    bound_action: str
    limit_status: str


@dataclass(frozen=True, slots=True)
class RevolvingCCFRow:
    default_id: str
    contract_id: str
    product_code: str
    observation_date: date
    default_date: date
    horizon_months: int
    observed_balance: Decimal
    observed_limit: Decimal
    available_limit: Decimal
    utilization: Decimal
    limit_at_default: Decimal
    limit_status: str
    ead_at_default: Decimal
    incremental_drawdown: Decimal
    raw_ccf: Decimal | None
    target_ccf: Decimal | None
    split: str
    policy_version: str
    policy_sha256: str


@dataclass(frozen=True, slots=True)
class RevolvingCCFDataset:
    rows: tuple[RevolvingCCFRow, ...]
    version: str
    defaults: int
    skipped_missing_horizon: int
    policy_version: str
    policy_sha256: str


@dataclass(frozen=True, slots=True)
class CCFCoefficient:
    feature: str
    coefficient: float


@dataclass(frozen=True, slots=True)
class CCFModelMetrics:
    observations: int
    mean_actual: float
    mean_prediction: float
    mean_absolute_error: float
    root_mean_squared_error: float
    minimum_prediction: float
    maximum_prediction: float


@dataclass(frozen=True, slots=True)
class RevolvingCCFModel:
    name: str
    pipeline: Any
    coefficients: tuple[CCFCoefficient, ...]
    training_metrics: CCFModelMetrics
    status: str
    rationale: str
    policy_version: str
    policy_sha256: str


def load_revolving_ccf_policy(path: Path) -> RevolvingCCFPolicy:
    raw = path.read_bytes()
    document = json.loads(raw)
    if document["schema_version"] != "1.0.0":
        raise DomainValidationError("unsupported revolving CCF policy schema")
    horizons = tuple(int(item) for item in document["horizons_months"])
    lower = Decimal(document["lower_bound"])
    upper = Decimal(document["upper_bound"])
    development = document["development_population"]
    if not horizons or any(item <= 0 for item in horizons) or len(set(horizons)) != len(horizons):
        raise DomainValidationError("CCF horizons must be unique and positive")
    if lower < 0 or upper > 1 or lower >= upper:
        raise DomainValidationError("CCF bounds are invalid")
    return RevolvingCCFPolicy(
        document["policy_version"],
        date.fromisoformat(document["effective_from"]),
        document["evidence_status"],
        horizons,
        lower,
        upper,
        document["zero_available_limit_treatment"],
        document["out_of_bounds_treatment"],
        int(development["seed"]),
        int(development["clients"]),
        int(development["contracts_per_client"]),
        sha256(raw).hexdigest(),
    )


def calculate_realized_ccf(
    *,
    observation_date: date,
    default_date: date,
    observed_balance: Decimal,
    observed_limit: Decimal,
    limit_at_default: Decimal,
    ead_at_default: Decimal,
    policy: RevolvingCCFPolicy,
) -> RealizedCCF:
    if observation_date >= default_date:
        raise DomainValidationError("CCF observation must precede default")
    if any(
        item < 0 for item in (observed_balance, observed_limit, limit_at_default, ead_at_default)
    ):
        raise DomainValidationError("CCF balances and limits must be non-negative")
    if observed_balance > observed_limit or ead_at_default > limit_at_default:
        raise DomainValidationError("CCF balance or EAD exceeds the applicable limit")
    available = observed_limit - observed_balance
    incremental = max(Decimal("0"), ead_at_default - observed_balance)
    if limit_at_default == 0:
        limit_status = "cancelled"
    elif limit_at_default < observed_limit:
        limit_status = "reduced"
    elif limit_at_default > observed_limit:
        limit_status = "increased"
    else:
        limit_status = "unchanged"
    if available == 0:
        return RealizedCCF(
            observed_balance,
            observed_limit,
            available,
            limit_at_default,
            ead_at_default,
            incremental,
            None,
            None,
            False,
            "undefined_zero_available_limit",
            limit_status,
        )
    raw = (incremental / available).quantize(QUANTUM, rounding=ROUND_HALF_EVEN)
    if raw < policy.lower_bound:
        bounded = policy.lower_bound
        action = "floored_at_zero"
    elif raw > policy.upper_bound:
        bounded = policy.upper_bound
        action = "capped_at_one"
    else:
        bounded = raw
        action = "none"
    return RealizedCCF(
        observed_balance,
        observed_limit,
        available,
        limit_at_default,
        ead_at_default,
        incremental,
        raw,
        bounded,
        True,
        action,
        limit_status,
    )


def _split(value: date) -> str:
    return "train" if value.year <= 2021 else "validation"


def build_revolving_ccf_dataset(
    population: SyntheticPortfolio,
    history: LongitudinalPortfolio,
    events: CreditEventHistory,
    policy: RevolvingCCFPolicy,
) -> RevolvingCCFDataset:
    contracts = {item.contract_id: item for item in population.contracts}
    snapshots: dict[str, dict[date, MonthlySnapshotRecord]] = {}
    for item in history.snapshots:
        snapshots.setdefault(item.contract_id, {})[item.reference_date] = item
    rows: list[RevolvingCCFRow] = []
    default_count = 0
    skipped = 0
    for default in events.defaults:
        contract = contracts[default.contract_id]
        if default.is_redefault or contract.facility_type != "revolving":
            continue
        default_count += 1
        contract_snapshots = snapshots[default.contract_id]
        before_default = [
            item for value, item in contract_snapshots.items() if value < default.default_date
        ]
        if not before_default:
            raise DomainValidationError("revolving default has no prior snapshot")
        default_snapshot = max(before_default, key=lambda item: item.reference_date)
        for horizon in policy.horizons_months:
            observation_date = _add_months(default.default_date, -horizon)
            observation = contract_snapshots.get(observation_date)
            if observation is None:
                skipped += 1
                continue
            measurement = calculate_realized_ccf(
                observation_date=observation.reference_date,
                default_date=default.default_date,
                observed_balance=observation.balance,
                observed_limit=observation.credit_limit,
                limit_at_default=default_snapshot.credit_limit,
                ead_at_default=default.exposure_at_default,
                policy=policy,
            )
            rows.append(
                RevolvingCCFRow(
                    default.default_id,
                    default.contract_id,
                    contract.product_code,
                    observation.reference_date,
                    default.default_date,
                    horizon,
                    observation.balance,
                    observation.credit_limit,
                    measurement.available_limit,
                    observation.utilization,
                    default_snapshot.credit_limit,
                    measurement.limit_status,
                    default.exposure_at_default,
                    measurement.incremental_drawdown,
                    measurement.raw_ccf,
                    measurement.realized_ccf,
                    _split(default.default_date),
                    policy.policy_version,
                    policy.sha256,
                )
            )
    return RevolvingCCFDataset(
        tuple(rows), "0.1.0", default_count, skipped, policy.policy_version, policy.sha256
    )


def _frame(rows: list[RevolvingCCFRow]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "utilization": float(item.utilization),
                "horizon_months": float(item.horizon_months),
                "utilization_horizon_interaction": float(item.utilization) * item.horizon_months,
                "product_code": item.product_code,
                "limit_status": item.limit_status,
            }
            for item in rows
        ]
    )


def fit_revolving_ccf_model(dataset: RevolvingCCFDataset) -> RevolvingCCFModel:
    rows = [item for item in dataset.rows if item.split == "train" and item.target_ccf is not None]
    if len(rows) < 5:
        raise DomainValidationError("revolving CCF training sample is insufficient")
    transformer = ColumnTransformer(
        (
            ("numeric", StandardScaler(), list(NUMERIC_FEATURES)),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                list(CATEGORICAL_FEATURES),
            ),
        )
    )
    pipeline = Pipeline((("features", transformer), ("model", Ridge(alpha=5.0))))
    actual = np.asarray([float(cast(Decimal, item.target_ccf)) for item in rows])
    pipeline.fit(_frame(rows), actual)
    prediction = np.clip(pipeline.predict(_frame(rows)), 0.0, 1.0)
    errors = prediction - actual
    feature_names = pipeline.named_steps["features"].get_feature_names_out()
    coefficients = pipeline.named_steps["model"].coef_
    return RevolvingCCFModel(
        "ridge_product_utilization_horizon",
        pipeline,
        tuple(
            CCFCoefficient(str(feature), float(value))
            for feature, value in zip(feature_names, coefficients, strict=True)
        ),
        CCFModelMetrics(
            len(rows),
            float(actual.mean()),
            float(prediction.mean()),
            float(np.abs(errors).mean()),
            sqrt(float(np.square(errors).mean())),
            float(prediction.min()),
            float(prediction.max()),
        ),
        "demonstrative_not_approved",
        "Deterministic synthetic development fit; limit reductions are supported but absent "
        "from estimation data.",
        dataset.policy_version,
        dataset.policy_sha256,
    )


def predict_revolving_ccf(
    model: RevolvingCCFModel, rows: tuple[RevolvingCCFRow, ...]
) -> tuple[float, ...]:
    if not rows:
        return ()
    prediction = np.clip(model.pipeline.predict(_frame(list(rows))), 0.0, 1.0)
    return tuple(float(item) for item in prediction)
