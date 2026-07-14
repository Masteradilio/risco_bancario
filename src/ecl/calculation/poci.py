"""POCI classification, credit-adjusted EIR and lifetime ECL changes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal
from typing import cast

from ...domain.conventions import DecimalInput, money, non_empty
from ...domain.exceptions import DomainValidationError
from ...domain.scenarios import ScenarioKind, ScenarioSet

RATE_QUANTUM = Decimal("0.00000001")


@dataclass(frozen=True, slots=True)
class POCICashFlow:
    payment_date: date
    amount: DecimalInput

    def __post_init__(self) -> None:
        object.__setattr__(self, "amount", money(self.amount, field="poci_cashflow"))


@dataclass(frozen=True, slots=True)
class POCIClassification:
    contract_id: str
    is_poci: bool
    classification_reason: str | None


@dataclass(frozen=True, slots=True)
class POCIMeasurement:
    contract_id: str
    recognition_date: date
    credit_adjusted_eir: Decimal
    initial_lifetime_ecl: Decimal
    current_lifetime_ecl: Decimal
    cumulative_lifetime_ecl_change: Decimal
    change_classification: str
    status: str


@dataclass(frozen=True, slots=True)
class POCIScenarioCashFlows:
    scenario_id: str
    expected_cashflows: tuple[POCICashFlow, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "scenario_id", non_empty(self.scenario_id, field="scenario_id"))


@dataclass(frozen=True, slots=True)
class POCIScenarioResult:
    scenario_id: str
    kind: ScenarioKind
    weight: Decimal
    initial_lifetime_ecl: Decimal
    current_lifetime_ecl: Decimal
    lifetime_ecl_change: Decimal
    change_classification: str
    weighted_ecl_contribution: Decimal
    weighted_change_contribution: Decimal


@dataclass(frozen=True, slots=True)
class POCIScenarioMeasurement:
    contract_id: str
    recognition_date: date
    credit_adjusted_eir: Decimal
    scenario_results: tuple[POCIScenarioResult, ...]
    probability_weighted_lifetime_ecl: Decimal
    probability_weighted_lifetime_change: Decimal
    stress_lifetime_ecl: Decimal
    presentation: str
    interest_presentation_basis: str
    scenario_version: str
    scenario_source_hash: str
    status: str


def classify_poci(
    contract_id: str,
    *,
    acquired_credit_impaired: bool,
    originated_credit_impaired: bool,
) -> POCIClassification:
    normalized = non_empty(contract_id, field="contract_id")
    reason = None
    if acquired_credit_impaired:
        reason = "acquired_credit_impaired"
    elif originated_credit_impaired:
        reason = "originated_credit_impaired"
    return POCIClassification(normalized, reason is not None, reason)


def _validate_cashflows(
    recognition_date: date,
    contractual: tuple[POCICashFlow, ...],
    expected: tuple[POCICashFlow, ...],
) -> None:
    if not contractual or len(contractual) != len(expected):
        raise DomainValidationError("POCI contractual and expected cash flows must align")
    if any(item.payment_date <= recognition_date for item in contractual):
        raise DomainValidationError("POCI cash flows must be after recognition")
    if [item.payment_date for item in contractual] != [item.payment_date for item in expected]:
        raise DomainValidationError("POCI expected dates must match contractual dates")
    if any(cast(Decimal, item.amount) < 0 for item in (*contractual, *expected)):
        raise DomainValidationError("POCI cash flows must be non-negative")
    if any(
        cast(Decimal, expected_item.amount) > cast(Decimal, contractual_item.amount)
        for contractual_item, expected_item in zip(contractual, expected, strict=True)
    ):
        raise DomainValidationError("POCI expected cash flow cannot exceed contractual cash flow")


def _present_value(
    cashflows: tuple[POCICashFlow, ...], recognition_date: date, annual_rate: float
) -> Decimal:
    value = sum(
        float(cast(Decimal, item.amount))
        / (1 + annual_rate) ** ((item.payment_date - recognition_date).days / 365)
        for item in cashflows
    )
    return Decimal(str(value)).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_EVEN)


def credit_adjusted_eir(
    purchase_price: DecimalInput,
    recognition_date: date,
    initial_expected_cashflows: tuple[POCICashFlow, ...],
) -> Decimal:
    price = money(purchase_price, field="purchase_price")
    if not initial_expected_cashflows or any(
        item.payment_date <= recognition_date for item in initial_expected_cashflows
    ):
        raise DomainValidationError("initial expected cash flows must follow recognition")
    low = -0.99
    high = 10.0
    if _present_value(initial_expected_cashflows, recognition_date, low) < price:
        raise DomainValidationError("purchase price cannot be reconciled to expected cash flows")
    if _present_value(initial_expected_cashflows, recognition_date, high) > price:
        raise DomainValidationError("credit-adjusted EIR exceeds supported search range")
    for _ in range(200):
        middle = (low + high) / 2
        if _present_value(initial_expected_cashflows, recognition_date, middle) > price:
            low = middle
        else:
            high = middle
    return Decimal(str((low + high) / 2)).quantize(RATE_QUANTUM, rounding=ROUND_HALF_EVEN)


def measure_poci_change(
    contract_id: str,
    recognition_date: date,
    purchase_price: DecimalInput,
    contractual_cashflows: tuple[POCICashFlow, ...],
    initial_expected_cashflows: tuple[POCICashFlow, ...],
    current_expected_cashflows: tuple[POCICashFlow, ...],
) -> POCIMeasurement:
    _validate_cashflows(recognition_date, contractual_cashflows, initial_expected_cashflows)
    _validate_cashflows(recognition_date, contractual_cashflows, current_expected_cashflows)
    eir = credit_adjusted_eir(purchase_price, recognition_date, initial_expected_cashflows)
    contractual_pv = _present_value(contractual_cashflows, recognition_date, float(eir))
    initial_expected_pv = _present_value(initial_expected_cashflows, recognition_date, float(eir))
    current_expected_pv = _present_value(current_expected_cashflows, recognition_date, float(eir))
    initial_ecl = contractual_pv - initial_expected_pv
    current_ecl = contractual_pv - current_expected_pv
    change = current_ecl - initial_ecl
    classification = (
        "impairment_loss" if change > 0 else "impairment_gain" if change < 0 else "no_change"
    )
    return POCIMeasurement(
        non_empty(contract_id, field="contract_id"),
        recognition_date,
        eir,
        initial_ecl,
        current_ecl,
        change,
        classification,
        "synthetic_unapproved",
    )


def measure_poci_scenarios(
    contract_id: str,
    recognition_date: date,
    purchase_price: DecimalInput,
    contractual_cashflows: tuple[POCICashFlow, ...],
    initial_expected_cashflows: tuple[POCICashFlow, ...],
    scenario_cashflows: tuple[POCIScenarioCashFlows, ...],
    scenario_set: ScenarioSet,
) -> POCIScenarioMeasurement:
    normalized_contract_id = non_empty(contract_id, field="contract_id")
    _validate_cashflows(recognition_date, contractual_cashflows, initial_expected_cashflows)
    expected_ids = {trajectory.scenario_id for trajectory in scenario_set.trajectories}
    actual_ids = [item.scenario_id for item in scenario_cashflows]
    if set(actual_ids) != expected_ids or len(actual_ids) != len(set(actual_ids)):
        raise DomainValidationError("POCI cash flows must cover each scenario exactly once")
    for item in scenario_cashflows:
        _validate_cashflows(recognition_date, contractual_cashflows, item.expected_cashflows)
    adjusted_eir = credit_adjusted_eir(purchase_price, recognition_date, initial_expected_cashflows)
    contractual_pv = _present_value(contractual_cashflows, recognition_date, float(adjusted_eir))
    initial_pv = _present_value(initial_expected_cashflows, recognition_date, float(adjusted_eir))
    initial_ecl = contractual_pv - initial_pv
    trajectories = {item.scenario_id: item for item in scenario_set.trajectories}
    results: list[POCIScenarioResult] = []
    for item in scenario_cashflows:
        trajectory = trajectories[item.scenario_id]
        current_pv = _present_value(item.expected_cashflows, recognition_date, float(adjusted_eir))
        current_ecl = contractual_pv - current_pv
        change = current_ecl - initial_ecl
        classification = (
            "impairment_loss" if change > 0 else "impairment_gain" if change < 0 else "no_change"
        )
        weight = Decimal(str(trajectory.weight))
        results.append(
            POCIScenarioResult(
                item.scenario_id,
                trajectory.kind,
                weight,
                initial_ecl,
                current_ecl,
                change,
                classification,
                (current_ecl * weight).quantize(RATE_QUANTUM, rounding=ROUND_HALF_EVEN),
                (change * weight).quantize(RATE_QUANTUM, rounding=ROUND_HALF_EVEN),
            )
        )
    probabilistic = tuple(item for item in results if item.kind != ScenarioKind.STRESS)
    weighted_ecl = sum(
        (item.weighted_ecl_contribution for item in probabilistic), Decimal("0")
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    weighted_change = sum(
        (item.weighted_change_contribution for item in probabilistic), Decimal("0")
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    presentation = (
        "impairment_loss"
        if weighted_change > 0
        else "impairment_gain" if weighted_change < 0 else "no_change"
    )
    stress_ecl = next(
        item.current_lifetime_ecl for item in results if item.kind == ScenarioKind.STRESS
    )
    return POCIScenarioMeasurement(
        normalized_contract_id,
        recognition_date,
        adjusted_eir,
        tuple(results),
        weighted_ecl,
        weighted_change,
        stress_ecl,
        presentation,
        "credit_adjusted_eir_on_amortized_cost",
        scenario_set.version,
        scenario_set.source_snapshot_hash,
        "synthetic_unapproved",
    )
