from datetime import date
from decimal import Decimal

import pytest

from src.domain.exceptions import DomainValidationError
from src.regulatory.cmn4966 import (
    ProvisionMethodology,
    ProvisionPortfolio,
    PrudentialSegment,
    RegulatoryFramework,
    calculate_simplified_provision,
    load_simplified_provision_policy,
    resolve_methodology,
)

REFERENCE_DATE = date(2026, 7, 31)


def _simplified(segment: PrudentialSegment = PrudentialSegment.S4):
    return resolve_methodology(
        framework=RegulatoryFramework.CMN4966,
        segment=segment,
    )


@pytest.mark.parametrize(
    "segment", [PrudentialSegment.S1, PrudentialSegment.S2, PrudentialSegment.S3]
)
def test_s1_to_s3_route_to_complete_methodology(segment: PrudentialSegment) -> None:
    assert _simplified(segment).methodology == ProvisionMethodology.COMPLETE


def test_s4_and_s5_route_to_simplified_unless_official_exception_applies() -> None:
    assert _simplified(PrudentialSegment.S4).methodology == ProvisionMethodology.SIMPLIFIED
    assert _simplified(PrudentialSegment.S5).methodology == ProvisionMethodology.SIMPLIFIED
    authorized_s4 = resolve_methodology(
        framework=RegulatoryFramework.BCB352,
        segment=PrudentialSegment.S4,
        has_complete_method_authorization=True,
    )
    assert authorized_s4.methodology == ProvisionMethodology.COMPLETE
    assert authorized_s4.requires_bcb_authorization


def test_cooperative_system_exceptions_route_to_complete_methodology() -> None:
    with_s3 = resolve_methodology(
        framework=RegulatoryFramework.CMN4966,
        segment=PrudentialSegment.S5,
        is_credit_cooperative=True,
        cooperative_system_segments=(PrudentialSegment.S3, PrudentialSegment.S5),
    )
    authorized_central = resolve_methodology(
        framework=RegulatoryFramework.CMN4966,
        segment=PrudentialSegment.S5,
        is_credit_cooperative=True,
        cooperative_system_segments=(PrudentialSegment.S4, PrudentialSegment.S5),
        cooperative_central_has_complete_authorization=True,
    )
    assert with_s3.methodology == ProvisionMethodology.COMPLETE
    assert authorized_central.methodology == ProvisionMethodology.COMPLETE


def test_invalid_authorization_and_cooperative_facts_fail_closed() -> None:
    with pytest.raises(DomainValidationError, match="restricted to S4"):
        resolve_methodology(
            framework=RegulatoryFramework.CMN4966,
            segment=PrudentialSegment.S5,
            has_complete_method_authorization=True,
        )
    with pytest.raises(DomainValidationError, match="require a credit cooperative"):
        resolve_methodology(
            framework=RegulatoryFramework.CMN4966,
            segment=PrudentialSegment.S4,
            cooperative_system_segments=(PrudentialSegment.S4,),
        )


def test_simplified_policy_is_versioned_and_contains_official_annex_ii_rates() -> None:
    policy = load_simplified_provision_policy(REFERENCE_DATE)
    assert policy.policy_version == "2025.01.1"
    assert policy.maximum_days == (14, 30, 60, 90)
    assert dict(policy.non_problem_rates)[ProvisionPortfolio.C5] == (
        Decimal("0.01900000"),
        Decimal("0.07500000"),
        Decimal("0.15000000"),
        Decimal("0.38000000"),
    )
    assert len(policy.sha256) == 64


def test_all_simplified_regulatory_rates_match_the_official_source() -> None:
    policy = load_simplified_provision_policy(REFERENCE_DATE)
    assert dict(policy.non_problem_rates) == {
        ProvisionPortfolio.C1: tuple(map(Decimal, ("0.014", "0.035", "0.045", "0.050"))),
        ProvisionPortfolio.C2: tuple(map(Decimal, ("0.014", "0.035", "0.060", "0.170"))),
        ProvisionPortfolio.C3: tuple(map(Decimal, ("0.019", "0.035", "0.130", "0.320"))),
        ProvisionPortfolio.C4: tuple(map(Decimal, ("0.019", "0.035", "0.130", "0.320"))),
        ProvisionPortfolio.C5: tuple(map(Decimal, ("0.019", "0.075", "0.150", "0.380"))),
    }
    assert dict(policy.problem_non_delinquent_rates) == dict(
        zip(
            ProvisionPortfolio,
            map(Decimal, ("0.100", "0.334", "0.487", "0.395", "0.534")),
            strict=True,
        )
    )
    assert dict(policy.delinquent_rates) == dict(
        zip(
            ProvisionPortfolio,
            map(Decimal, ("0.045", "0.034", "0.037", "0.045", "0.034")),
            strict=True,
        )
    )


def test_non_problem_simplified_provision_keeps_components_separate() -> None:
    result = calculate_simplified_provision(
        applicability=_simplified(),
        reference_date=REFERENCE_DATE,
        portfolio=ProvisionPortfolio.C5,
        gross_carrying_amount="1000",
        estimated_expected_loss="50",
        days_past_due=10,
        problem_asset=False,
        default_date=None,
    )
    assert result.incurred_loss_floor == Decimal("0.00")
    assert result.additional_expected_loss_floor == Decimal("19.00")
    assert result.regulatory_minimum == Decimal("19.00")
    assert result.excess_expected_loss == Decimal("31.00")
    assert result.final_provision == Decimal("50.00")


def test_problem_and_delinquent_rules_are_additive_and_capped() -> None:
    problem = calculate_simplified_provision(
        applicability=_simplified(),
        reference_date=REFERENCE_DATE,
        portfolio=ProvisionPortfolio.C2,
        gross_carrying_amount="1000",
        estimated_expected_loss="200",
        days_past_due=30,
        problem_asset=True,
        default_date=None,
    )
    delinquent = calculate_simplified_provision(
        applicability=_simplified(),
        reference_date=REFERENCE_DATE,
        portfolio=ProvisionPortfolio.C5,
        gross_carrying_amount="1000",
        estimated_expected_loss="400",
        days_past_due=120,
        problem_asset=True,
        default_date=date(2026, 7, 1),
    )
    assert problem.additional_expected_loss_floor == Decimal("334.00")
    assert problem.final_provision == Decimal("334.00")
    assert delinquent.incurred_loss_floor == Decimal("500.00")
    assert delinquent.additional_expected_loss_floor == Decimal("34.00")
    assert delinquent.regulatory_minimum == Decimal("534.00")
    assert delinquent.final_provision == Decimal("534.00")


def test_complete_route_and_inconsistent_default_state_are_rejected() -> None:
    common = {
        "reference_date": REFERENCE_DATE,
        "portfolio": ProvisionPortfolio.C1,
        "gross_carrying_amount": "1000",
        "estimated_expected_loss": "20",
        "default_date": date(2026, 7, 1),
    }
    with pytest.raises(DomainValidationError, match="rejects a complete"):
        calculate_simplified_provision(
            applicability=_simplified(PrudentialSegment.S2),
            days_past_due=120,
            problem_asset=True,
            **common,
        )
    with pytest.raises(DomainValidationError, match="must be characterized"):
        calculate_simplified_provision(
            applicability=_simplified(),
            days_past_due=120,
            problem_asset=False,
            **common,
        )
