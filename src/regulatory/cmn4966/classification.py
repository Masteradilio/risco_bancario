"""Business-model, SPPI, classification and prospective reclassification controls."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum

from ...domain.conventions import DecimalInput, money, non_empty
from ...domain.exceptions import DomainValidationError, TemporalConsistencyError


class BusinessModelObjective(StrEnum):
    HOLD_TO_COLLECT = "hold_to_collect"
    HOLD_TO_COLLECT_AND_SELL = "hold_to_collect_and_sell"
    OTHER = "other"


class MeasurementCategory(StrEnum):
    AMORTIZED_COST = "amortized_cost"
    FVOCI = "fvoci"
    FVTPL = "fvtpl"


class FinancialAssetKind(StrEnum):
    CREDIT_OPERATION = "credit_operation"
    PRIVATE_DEBT_SECURITY = "private_debt_security"
    OTHER_DEBT = "other_debt"
    EQUITY = "equity"
    DERIVATIVE = "derivative"


class ReclassificationRecognition(StrEnum):
    NONE = "none"
    PROFIT_OR_LOSS = "profit_or_loss"
    OCI = "other_comprehensive_income"
    REMOVE_OCI_AGAINST_ASSET = "remove_oci_against_asset"
    FAIR_VALUE_AS_NEW_GROSS_CARRYING_AMOUNT = "fair_value_as_new_gross_carrying_amount"


@dataclass(frozen=True, slots=True)
class BusinessModelRecord:
    model_id: str
    objective: BusinessModelObjective
    effective_from: date
    approved_by: str
    approval_date: date
    rationale: str

    def __post_init__(self) -> None:
        for field in ("model_id", "approved_by", "rationale"):
            object.__setattr__(self, field, non_empty(getattr(self, field), field=field))
        if self.approval_date > self.effective_from:
            raise TemporalConsistencyError(
                "business model must be approved before it becomes effective"
            )


@dataclass(frozen=True, slots=True)
class SPPITerms:
    principal_is_fair_value_at_initial_recognition: bool = True
    interest_is_time_value_and_credit_risk: bool = True
    includes_only_basic_lending_costs_and_margin: bool = True
    leveraged_return: bool = False
    equity_or_commodity_link: bool = False
    non_basic_currency_or_index_link: bool = False
    prepayment_is_principal_interest_and_reasonable_compensation: bool = True
    extension_preserves_basic_lending_return: bool = True


@dataclass(frozen=True, slots=True)
class SPPIAssessment:
    passed: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ClassificationResult:
    category: MeasurementCategory
    sppi: SPPIAssessment
    business_model_id: str
    impairment_eligible: bool
    impairment_rationale: str
    fvtpl_designated: bool
    source_locator: str = "Resolução CMN nº 4.966/2021, arts. 1º, 4º-8º"


@dataclass(frozen=True, slots=True)
class ReclassificationResult:
    previous_category: MeasurementCategory
    new_category: MeasurementCategory
    effective_date: date
    prospective: bool
    recognition: ReclassificationRecognition
    adjustment_amount: Decimal
    new_gross_carrying_amount: Decimal
    classification: ClassificationResult


def assess_sppi(terms: SPPITerms) -> SPPIAssessment:
    reasons: list[str] = []
    required = (
        (terms.principal_is_fair_value_at_initial_recognition, "principal_not_initial_fair_value"),
        (terms.interest_is_time_value_and_credit_risk, "interest_not_time_value_and_credit_risk"),
        (
            terms.includes_only_basic_lending_costs_and_margin,
            "non_basic_lending_cost_or_margin",
        ),
        (
            terms.prepayment_is_principal_interest_and_reasonable_compensation,
            "non_basic_prepayment_feature",
        ),
        (terms.extension_preserves_basic_lending_return, "non_basic_extension_feature"),
    )
    reasons.extend(reason for passed, reason in required if not passed)
    if terms.leveraged_return:
        reasons.append("leveraged_return")
    if terms.equity_or_commodity_link:
        reasons.append("equity_or_commodity_link")
    if terms.non_basic_currency_or_index_link:
        reasons.append("non_basic_currency_or_index_link")
    return SPPIAssessment(not reasons, tuple(reasons))


def _impairment_eligibility(
    kind: FinancialAssetKind,
    category: MeasurementCategory,
    fair_value_level: int | None,
) -> tuple[bool, str]:
    if kind in {FinancialAssetKind.EQUITY, FinancialAssetKind.DERIVATIVE}:
        return False, "equity instruments and derivatives are outside the ECL provision scope"
    if category != MeasurementCategory.FVTPL:
        return True, "debt asset at amortized cost or FVOCI is in the impairment scope"
    if kind in {FinancialAssetKind.CREDIT_OPERATION, FinancialAssetKind.PRIVATE_DEBT_SECURITY}:
        return True, "credit operations and private debt remain in scope at FVTPL"
    if fair_value_level not in {1, 2, 3}:
        raise DomainValidationError(
            "fair_value_level 1, 2 or 3 is required for other debt at FVTPL"
        )
    if fair_value_level == 1:
        return False, "level-1 FVTPL asset is excluded by the declared regulatory scope"
    return True, "non-level-1 FVTPL debt remains in the declared regulatory scope"


def classify_financial_asset(
    *,
    business_model: BusinessModelRecord,
    terms: SPPITerms,
    kind: FinancialAssetKind,
    fair_value_level: int | None = None,
    designate_fvtpl_for_accounting_mismatch: bool = False,
    designation_rationale: str | None = None,
) -> ClassificationResult:
    sppi = assess_sppi(terms)
    if designate_fvtpl_for_accounting_mismatch:
        if not designation_rationale or not designation_rationale.strip():
            raise DomainValidationError(
                "irrevocable FVTPL designation requires documented rationale"
            )
        category = MeasurementCategory.FVTPL
    elif kind == FinancialAssetKind.CREDIT_OPERATION:
        category = (
            MeasurementCategory.AMORTIZED_COST
            if business_model.objective != BusinessModelObjective.OTHER and sppi.passed
            else MeasurementCategory.FVTPL
        )
    elif business_model.objective == BusinessModelObjective.HOLD_TO_COLLECT and sppi.passed:
        category = MeasurementCategory.AMORTIZED_COST
    elif (
        business_model.objective == BusinessModelObjective.HOLD_TO_COLLECT_AND_SELL and sppi.passed
    ):
        category = MeasurementCategory.FVOCI
    else:
        category = MeasurementCategory.FVTPL
    eligible, rationale = _impairment_eligibility(kind, category, fair_value_level)
    return ClassificationResult(
        category,
        sppi,
        business_model.model_id,
        eligible,
        rationale,
        designate_fvtpl_for_accounting_mismatch,
    )


def _first_day_next_month(value: date) -> date:
    return date(value.year + (value.month == 12), value.month % 12 + 1, 1)


def reclassify_financial_asset(
    *,
    previous: ClassificationResult,
    new_business_model: BusinessModelRecord,
    change_date: date,
    terms: SPPITerms,
    kind: FinancialAssetKind,
    carrying_amount: DecimalInput,
    fair_value: DecimalInput,
    accumulated_oci: DecimalInput = "0",
    fair_value_level: int | None = None,
) -> ReclassificationResult:
    if previous.fvtpl_designated:
        raise DomainValidationError("an irrevocable FVTPL designation cannot be reclassified")
    if new_business_model.effective_from != _first_day_next_month(change_date):
        raise TemporalConsistencyError(
            "new business model must become effective on the first day of the next monthly period"
        )
    classification = classify_financial_asset(
        business_model=new_business_model,
        terms=terms,
        kind=kind,
        fair_value_level=fair_value_level,
    )
    carrying = money(carrying_amount, field="carrying_amount")
    fair = money(fair_value, field="fair_value")
    oci = money(accumulated_oci, field="accumulated_oci", allow_negative=True)
    previous_category = previous.category
    new_category = classification.category
    recognition = ReclassificationRecognition.NONE
    adjustment = Decimal("0.00")
    new_gross = carrying
    if previous_category == MeasurementCategory.AMORTIZED_COST:
        adjustment = fair - carrying
        new_gross = fair if new_category != previous_category else carrying
        if new_category == MeasurementCategory.FVTPL:
            recognition = ReclassificationRecognition.PROFIT_OR_LOSS
        elif new_category == MeasurementCategory.FVOCI:
            recognition = ReclassificationRecognition.OCI
    elif previous_category == MeasurementCategory.FVOCI:
        if new_category == MeasurementCategory.FVTPL:
            recognition = ReclassificationRecognition.PROFIT_OR_LOSS
            adjustment = oci
            new_gross = fair
        elif new_category == MeasurementCategory.AMORTIZED_COST:
            recognition = ReclassificationRecognition.REMOVE_OCI_AGAINST_ASSET
            adjustment = -oci
            new_gross = fair - oci
    elif previous_category == MeasurementCategory.FVTPL and new_category != previous_category:
        recognition = ReclassificationRecognition.FAIR_VALUE_AS_NEW_GROSS_CARRYING_AMOUNT
        new_gross = fair
    return ReclassificationResult(
        previous_category,
        new_category,
        new_business_model.effective_from,
        True,
        recognition,
        adjustment,
        new_gross,
        classification,
    )
