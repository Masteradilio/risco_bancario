"""Independent Decimal formulas for the published ECL golden-case package."""

from __future__ import annotations

import json
from decimal import ROUND_HALF_EVEN, Decimal, getcontext
from pathlib import Path
from typing import Any

CENT = Decimal("0.01")
RATE = Decimal("0.00000001")


def _decimal(value: Any) -> Decimal:
    return Decimal(str(value))


def _weighted(values: list[Any], weights: list[Any]) -> Decimal:
    return sum(
        (_decimal(value) * _decimal(weight) for value, weight in zip(values, weights, strict=True)),
        Decimal("0"),
    )


def _stage_periods(case: dict[str, Any], *, prepayment: bool) -> Decimal:
    survival = Decimal("1")
    prepayment_survival = Decimal("1")
    total = Decimal("0")
    hazards = case["inputs"]["hazards"]
    eads = case["inputs"]["eads"]
    discounts = case["inputs"]["discount_factors"]
    lgd = _decimal(case["inputs"]["lgd"])
    prepayment_rate = _decimal(case["inputs"].get("prepayment_rate", 0))
    for hazard_value, ead_value, discount_value in zip(hazards, eads, discounts, strict=True):
        hazard = _decimal(hazard_value)
        total += (
            survival
            * hazard
            * lgd
            * _decimal(ead_value)
            * _decimal(discount_value)
            * prepayment_survival
        )
        survival *= Decimal("1") - hazard
        if prepayment:
            prepayment_survival *= Decimal("1") - prepayment_rate
    return total


def _modification(case: dict[str, Any]) -> Decimal:
    inputs = case["inputs"]
    principal = _decimal(inputs["original_principal"])
    original_periods = int(inputs["original_periods"])
    elapsed = int(inputs["elapsed_periods"])
    revised_periods = int(inputs["revised_periods"])
    original_monthly = _decimal(inputs["original_rate"]) / Decimal("12")
    revised_monthly = _decimal(inputs["revised_rate"]) / Decimal("12")
    original_payment = (
        principal
        * original_monthly
        / (Decimal("1") - (Decimal("1") + original_monthly) ** -original_periods)
    )
    balance = principal
    for _ in range(elapsed):
        interest = (balance * original_monthly).quantize(CENT, rounding=ROUND_HALF_EVEN)
        principal_payment = (original_payment - interest).quantize(CENT, rounding=ROUND_HALF_EVEN)
        balance = (balance - principal_payment).quantize(CENT, rounding=ROUND_HALF_EVEN)
    revised_payment = (
        balance
        * revised_monthly
        / (Decimal("1") - (Decimal("1") + revised_monthly) ** -revised_periods)
    )
    hazard = _decimal(inputs["hazard"])
    lgd = _decimal(inputs["lgd"])
    total = Decimal("0")
    survival = Decimal("1")
    discount_eir = _decimal(inputs["discount_eir"])
    for period in range(1, revised_periods + 1):
        discount = (
            Decimal("1") / (Decimal("1") + discount_eir) ** (Decimal(period) / Decimal("12"))
        ).quantize(RATE, rounding=ROUND_HALF_EVEN)
        marginal_pd = (survival * hazard).quantize(RATE, rounding=ROUND_HALF_EVEN)
        total += (marginal_pd * lgd * balance * discount).quantize(CENT, rounding=ROUND_HALF_EVEN)
        survival = max(Decimal("0"), survival - marginal_pd)
        interest = (balance * revised_monthly).quantize(CENT, rounding=ROUND_HALF_EVEN)
        principal_payment = (revised_payment - interest).quantize(CENT, rounding=ROUND_HALF_EVEN)
        balance = (balance - principal_payment).quantize(CENT, rounding=ROUND_HALF_EVEN)
    return total


def calculate_case(case: dict[str, Any]) -> Decimal:
    """Calculate one published case without importing the production ECL engine."""
    formula = case["formula"]
    inputs = case["inputs"]
    if formula == "stage_periods":
        result = _stage_periods(case, prepayment=False)
    elif formula == "stage_periods_with_prepayment":
        result = _stage_periods(case, prepayment=True)
    elif formula == "cash_shortfall":
        result = (
            _decimal(inputs["contractual_cashflow"])
            - _decimal(inputs["borrower_cashflow"])
            - _decimal(inputs.get("collateral_recovery", 0))
            - _decimal(inputs.get("guarantee_recovery", 0))
            + _decimal(inputs.get("collection_costs", 0))
        )
    elif formula == "pd_lgd_ead_with_ccf":
        ead = _decimal(inputs["drawn_ead"]) + _decimal(inputs["undrawn_amount"]) * _decimal(
            inputs["ccf"]
        )
        result = _decimal(inputs["pd"]) * _decimal(inputs["lgd"]) * ead
    elif formula == "weighted_scenarios":
        result = _weighted(inputs["scenario_ecls"], inputs["weights"])
    elif formula == "modified_amortization":
        getcontext().prec = 40
        result = _modification(case)
    else:
        raise ValueError(f"unsupported golden-case formula: {formula}")
    return result.quantize(CENT, rounding=ROUND_HALF_EVEN)


def load_cases(path: Path) -> list[dict[str, Any]]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if document["schema_version"] != "1.0.0":
        raise ValueError("unsupported golden-case schema")
    return list(document["cases"])
