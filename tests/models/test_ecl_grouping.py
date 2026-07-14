from dataclasses import replace
from decimal import Decimal

import pytest

from src.domain.exceptions import DomainValidationError
from src.ecl.calculation import (
    ECLMeasurementRoute,
    GroupingMember,
    HomogeneousGroupDefinition,
    build_homogeneous_group_id,
    load_ecl_grouping_policy,
    route_ecl_measurement,
    validate_homogeneous_group,
)


def _member(index: int, *, ead: str | None = None) -> GroupingMember:
    return GroupingMember(
        f"CTR-{index:03d}",
        "mortgage",
        "residential_real_estate",
        2024,
        "performing_low_risk",
        "A2",
        str(Decimal("0.020") + Decimal(index % 3) * Decimal("0.0001")),
        str(Decimal("0.300") + Decimal(index % 2) * Decimal("0.001")),
        ead or str(Decimal("10000") + Decimal(index) * Decimal("10")),
    )


def _definition() -> HomogeneousGroupDefinition:
    return HomogeneousGroupDefinition(
        "mortgage_pool",
        ("product_code", "collateral_type", "vintage_bucket", "behavioral_risk_bucket"),
    )


def test_grouping_policy_is_versioned_and_demonstrative() -> None:
    policy = load_ecl_grouping_policy()
    assert policy.policy_version == "2026.07.1"
    assert policy.evidence_status == "synthetic_demonstrative_not_approved"
    assert policy.individual_ead_threshold == Decimal("500000.00")
    assert len(policy.sha256) == 64


def test_group_id_uses_economic_contractual_and_behavioral_dimensions() -> None:
    group_id = build_homogeneous_group_id(_member(1), _definition(), load_ecl_grouping_policy())
    assert "product_code=mortgage" in group_id
    assert "collateral_type=residential_real_estate" in group_id
    assert "vintage_bucket=2024-2025" in group_id
    assert "behavioral_risk_bucket=performing_low_risk" in group_id


def test_score_only_or_unknown_grouping_dimensions_are_rejected() -> None:
    policy = load_ecl_grouping_policy()
    with pytest.raises(DomainValidationError, match="cannot be based only"):
        build_homogeneous_group_id(
            _member(1), HomogeneousGroupDefinition("score_pool", ("score_band",)), policy
        )
    with pytest.raises(DomainValidationError, match="unsupported"):
        build_homogeneous_group_id(
            _member(1), HomogeneousGroupDefinition("bad", ("product_code", "region")), policy
        )


def test_low_dispersion_group_passes_statistical_homogeneity() -> None:
    members = tuple(_member(index) for index in range(20))
    report = validate_homogeneous_group(members, _definition(), load_ecl_grouping_policy())
    assert report.valid
    assert report.blockers == ()
    assert report.member_count == 20
    assert all(metric.passed for metric in report.metrics)
    assert report.maximum_single_exposure_share < Decimal("0.06")


def test_high_pd_dispersion_fails_homogeneity() -> None:
    members = list(_member(index) for index in range(20))
    members[-1] = replace(members[-1], pd_12m="0.90")
    report = validate_homogeneous_group(tuple(members), _definition(), load_ecl_grouping_policy())
    assert not report.valid
    assert "pd_12m_dispersion_above_limit" in report.blockers


def test_material_exposure_is_routed_to_individual_measurement() -> None:
    policy = load_ecl_grouping_policy()
    material = _member(1, ead="500000")
    assert route_ecl_measurement(material, policy) == ECLMeasurementRoute.INDIVIDUAL
    members = tuple([material] + [_member(index) for index in range(2, 21)])
    report = validate_homogeneous_group(members, _definition(), policy)
    assert "material_exposure_requires_individual_measurement" in report.blockers
    assert route_ecl_measurement(_member(2), policy) == ECLMeasurementRoute.COLLECTIVE_ELIGIBLE


def test_small_or_dimensionally_mixed_groups_fail_closed() -> None:
    policy = load_ecl_grouping_policy()
    small = validate_homogeneous_group(
        tuple(_member(index) for index in range(10)), _definition(), policy
    )
    assert not small.valid
    assert "group_below_minimum_size" in small.blockers
    mixed = tuple(_member(index) for index in range(19)) + (
        replace(_member(20), product_code="vehicle_finance"),
    )
    with pytest.raises(DomainValidationError, match="do not share"):
        validate_homogeneous_group(mixed, _definition(), policy)
