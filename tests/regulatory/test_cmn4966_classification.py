from dataclasses import replace
from datetime import date
from decimal import Decimal

import pytest

from src.domain.exceptions import DomainValidationError, TemporalConsistencyError
from src.regulatory.cmn4966 import (
    BusinessModelObjective,
    BusinessModelRecord,
    FinancialAssetKind,
    MeasurementCategory,
    ReclassificationRecognition,
    SPPITerms,
    assess_sppi,
    classify_financial_asset,
    reclassify_financial_asset,
)


def _model(objective: BusinessModelObjective, *, effective: date = date(2026, 1, 1)):
    return BusinessModelRecord(
        f"BM-{objective.value}",
        objective,
        effective,
        "Board",
        date(2025, 12, 15),
        "Approved portfolio management objective",
    )


def test_business_model_requires_prior_governance_approval() -> None:
    with pytest.raises(TemporalConsistencyError, match="approved before"):
        BusinessModelRecord(
            "BM-1",
            BusinessModelObjective.HOLD_TO_COLLECT,
            date(2026, 1, 1),
            "Board",
            date(2026, 1, 2),
            "Policy",
        )


def test_sppi_passes_basic_lending_terms_and_reports_every_failure() -> None:
    assert assess_sppi(SPPITerms()).passed
    failed = assess_sppi(
        SPPITerms(
            leveraged_return=True,
            equity_or_commodity_link=True,
            prepayment_is_principal_interest_and_reasonable_compensation=False,
        )
    )
    assert not failed.passed
    assert set(failed.reasons) == {
        "leveraged_return",
        "equity_or_commodity_link",
        "non_basic_prepayment_feature",
    }


@pytest.mark.parametrize(
    ("objective", "category"),
    [
        (BusinessModelObjective.HOLD_TO_COLLECT, MeasurementCategory.AMORTIZED_COST),
        (BusinessModelObjective.HOLD_TO_COLLECT_AND_SELL, MeasurementCategory.FVOCI),
        (BusinessModelObjective.OTHER, MeasurementCategory.FVTPL),
    ],
)
def test_debt_classification_combines_business_model_and_sppi(
    objective: BusinessModelObjective, category: MeasurementCategory
) -> None:
    result = classify_financial_asset(
        business_model=_model(objective),
        terms=SPPITerms(),
        kind=FinancialAssetKind.PRIVATE_DEBT_SECURITY,
    )
    assert result.category == category


def test_credit_operation_special_rule_and_failed_sppi_route_to_fvtpl() -> None:
    credit = classify_financial_asset(
        business_model=_model(BusinessModelObjective.HOLD_TO_COLLECT_AND_SELL),
        terms=SPPITerms(),
        kind=FinancialAssetKind.CREDIT_OPERATION,
    )
    failed = classify_financial_asset(
        business_model=_model(BusinessModelObjective.HOLD_TO_COLLECT),
        terms=replace(SPPITerms(), leveraged_return=True),
        kind=FinancialAssetKind.CREDIT_OPERATION,
    )
    assert credit.category == MeasurementCategory.AMORTIZED_COST
    assert failed.category == MeasurementCategory.FVTPL
    assert failed.impairment_eligible


def test_irrevocable_fvtpl_designation_requires_documented_mismatch() -> None:
    with pytest.raises(DomainValidationError, match="documented rationale"):
        classify_financial_asset(
            business_model=_model(BusinessModelObjective.HOLD_TO_COLLECT),
            terms=SPPITerms(),
            kind=FinancialAssetKind.OTHER_DEBT,
            designate_fvtpl_for_accounting_mismatch=True,
        )
    result = classify_financial_asset(
        business_model=_model(BusinessModelObjective.HOLD_TO_COLLECT),
        terms=SPPITerms(),
        kind=FinancialAssetKind.OTHER_DEBT,
        fair_value_level=2,
        designate_fvtpl_for_accounting_mismatch=True,
        designation_rationale="Eliminates an existing measurement mismatch",
    )
    assert result.category == MeasurementCategory.FVTPL
    assert result.fvtpl_designated


def test_impairment_eligibility_is_explicit_for_fvtpl_scope_exclusions() -> None:
    level_one = classify_financial_asset(
        business_model=_model(BusinessModelObjective.OTHER),
        terms=SPPITerms(),
        kind=FinancialAssetKind.OTHER_DEBT,
        fair_value_level=1,
    )
    derivative = classify_financial_asset(
        business_model=_model(BusinessModelObjective.OTHER),
        terms=SPPITerms(),
        kind=FinancialAssetKind.DERIVATIVE,
    )
    assert not level_one.impairment_eligible
    assert not derivative.impairment_eligible


def test_reclassification_is_prospective_on_first_day_of_next_period() -> None:
    previous = classify_financial_asset(
        business_model=_model(BusinessModelObjective.HOLD_TO_COLLECT),
        terms=SPPITerms(),
        kind=FinancialAssetKind.PRIVATE_DEBT_SECURITY,
    )
    new_model = _model(BusinessModelObjective.HOLD_TO_COLLECT_AND_SELL, effective=date(2026, 8, 1))
    result = reclassify_financial_asset(
        previous=previous,
        new_business_model=new_model,
        change_date=date(2026, 7, 14),
        terms=SPPITerms(),
        kind=FinancialAssetKind.PRIVATE_DEBT_SECURITY,
        carrying_amount="1000",
        fair_value="1030",
    )
    assert result.previous_category == MeasurementCategory.AMORTIZED_COST
    assert result.new_category == MeasurementCategory.FVOCI
    assert result.effective_date == date(2026, 8, 1)
    assert result.prospective
    assert result.recognition == ReclassificationRecognition.OCI
    assert result.adjustment_amount == Decimal("30.00")


def test_fvoci_to_amortized_cost_removes_oci_against_asset() -> None:
    previous = classify_financial_asset(
        business_model=_model(BusinessModelObjective.HOLD_TO_COLLECT_AND_SELL),
        terms=SPPITerms(),
        kind=FinancialAssetKind.PRIVATE_DEBT_SECURITY,
    )
    result = reclassify_financial_asset(
        previous=previous,
        new_business_model=_model(
            BusinessModelObjective.HOLD_TO_COLLECT, effective=date(2026, 8, 1)
        ),
        change_date=date(2026, 7, 31),
        terms=SPPITerms(),
        kind=FinancialAssetKind.PRIVATE_DEBT_SECURITY,
        carrying_amount="1030",
        fair_value="1030",
        accumulated_oci="30",
    )
    assert result.recognition == ReclassificationRecognition.REMOVE_OCI_AGAINST_ASSET
    assert result.adjustment_amount == Decimal("-30.00")
    assert result.new_gross_carrying_amount == Decimal("1000.00")


def test_fvtpl_to_amortized_cost_uses_fair_value_as_new_gross_amount() -> None:
    previous = classify_financial_asset(
        business_model=_model(BusinessModelObjective.OTHER),
        terms=SPPITerms(),
        kind=FinancialAssetKind.PRIVATE_DEBT_SECURITY,
    )
    result = reclassify_financial_asset(
        previous=previous,
        new_business_model=_model(
            BusinessModelObjective.HOLD_TO_COLLECT, effective=date(2026, 8, 1)
        ),
        change_date=date(2026, 7, 14),
        terms=SPPITerms(),
        kind=FinancialAssetKind.PRIVATE_DEBT_SECURITY,
        carrying_amount="1020",
        fair_value="1025",
    )
    assert result.recognition == ReclassificationRecognition.FAIR_VALUE_AS_NEW_GROSS_CARRYING_AMOUNT
    assert result.new_gross_carrying_amount == Decimal("1025.00")


def test_irrevocably_designated_fvtpl_asset_cannot_be_reclassified() -> None:
    previous = classify_financial_asset(
        business_model=_model(BusinessModelObjective.HOLD_TO_COLLECT),
        terms=SPPITerms(),
        kind=FinancialAssetKind.OTHER_DEBT,
        fair_value_level=2,
        designate_fvtpl_for_accounting_mismatch=True,
        designation_rationale="Existing accounting mismatch",
    )
    with pytest.raises(DomainValidationError, match="irrevocable"):
        reclassify_financial_asset(
            previous=previous,
            new_business_model=_model(
                BusinessModelObjective.HOLD_TO_COLLECT_AND_SELL,
                effective=date(2026, 8, 1),
            ),
            change_date=date(2026, 7, 14),
            terms=SPPITerms(),
            kind=FinancialAssetKind.OTHER_DEBT,
            carrying_amount="1000",
            fair_value="1005",
            fair_value_level=2,
        )


def test_reclassification_rejects_non_subsequent_effective_date() -> None:
    previous = classify_financial_asset(
        business_model=_model(BusinessModelObjective.HOLD_TO_COLLECT),
        terms=SPPITerms(),
        kind=FinancialAssetKind.PRIVATE_DEBT_SECURITY,
    )
    with pytest.raises(TemporalConsistencyError, match="first day"):
        reclassify_financial_asset(
            previous=previous,
            new_business_model=_model(BusinessModelObjective.OTHER, effective=date(2026, 7, 15)),
            change_date=date(2026, 7, 14),
            terms=SPPITerms(),
            kind=FinancialAssetKind.PRIVATE_DEBT_SECURITY,
            carrying_amount="1000",
            fair_value="1010",
        )
