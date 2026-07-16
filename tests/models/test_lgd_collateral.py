import json
from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from src.data.synthetic.population import CollateralRecord
from src.domain.exceptions import DomainValidationError
from src.models.lgd import (
    LGDWorkoutRecord,
    WorkoutCashFlow,
    load_collateral_policy,
    project_collateral_recovery,
    project_collateral_sensitivities,
)

POLICY_PATH = Path("config/lgd_collateral_policy/2026.07.1.json")


def _cashflow(source: str, net: Decimal) -> WorkoutCashFlow:
    return WorkoutCashFlow(date(2026, 1, 1), source, net, Decimal("0"), net, False)


def _record(
    *,
    rate: Decimal = Decimal("0"),
    cashflows: tuple[WorkoutCashFlow, ...] = (),
) -> LGDWorkoutRecord:
    gross = sum((item.gross_amount for item in cashflows), Decimal("0"))
    costs = sum((item.cost_amount for item in cashflows), Decimal("0"))
    return LGDWorkoutRecord(
        "DEF-001",
        "CTR-001",
        date(2026, 1, 1),
        "2026-Q1",
        "mortgage",
        Decimal("100"),
        rate,
        24,
        date(2028, 1, 1),
        date(2028, 1, 1),
        False,
        False,
        "open_complete",
        None,
        None,
        Decimal("0"),
        "real_estate",
        Decimal("120"),
        Decimal("0.9"),
        gross,
        costs,
        gross - costs,
        cashflows,
    )


def _collateral() -> CollateralRecord:
    return CollateralRecord(
        "COL-001",
        "CTR-001",
        "real_estate",
        date(2026, 1, 1),
        Decimal("120"),
        Decimal("0.9"),
        "BRL",
    )


def test_projects_value_haircut_cost_and_execution_time() -> None:
    result = project_collateral_recovery(
        _record(), _collateral(), load_collateral_policy(POLICY_PATH)
    )

    assert result.value_at_default == Decimal("120.00000000")
    assert result.enforceable_value == Decimal("108.00000000")
    assert result.haircut == Decimal("0.25000000")
    assert result.projected_gross_recovery == Decimal("81.00000000")
    assert result.projected_execution_cost == Decimal("9.72000000")
    assert result.execution_date == date(2027, 1, 1)
    assert result.projected_discounted_net_recovery == Decimal("71.28000000")


def test_discounts_projected_collateral_at_contractual_eir() -> None:
    result = project_collateral_recovery(
        _record(rate=Decimal("0.10")),
        _collateral(),
        load_collateral_policy(POLICY_PATH),
    )

    assert result.projected_discounted_net_recovery == Decimal("64.80000000")


def test_excludes_observed_collateral_cashflow_instead_of_double_counting() -> None:
    record = _record(
        cashflows=(
            _cashflow("cash_collection", Decimal("20")),
            _cashflow("collateral_execution", Decimal("50")),
        )
    )

    result = project_collateral_recovery(record, _collateral(), load_collateral_policy(POLICY_PATH))

    assert result.discounted_noncollateral_recovery == Decimal("20.00000000")
    assert result.excluded_observed_collateral_recovery == Decimal("50.00000000")
    assert result.collateral_recovery_used == Decimal("71.28000000")
    assert result.combined_discounted_recovery == Decimal("91.28000000")


def test_caps_collateral_at_remaining_ead_headroom() -> None:
    record = _record(cashflows=(_cashflow("cash_collection", Decimal("90")),))

    result = project_collateral_recovery(record, _collateral(), load_collateral_policy(POLICY_PATH))

    assert result.collateral_recovery_used == Decimal("10.00000000")
    assert result.combined_discounted_recovery == Decimal("100.00000000")


def test_sensitivities_are_ordered_and_retain_policy_lineage() -> None:
    policy = load_collateral_policy(POLICY_PATH)

    upside, base, downside = project_collateral_sensitivities(_record(), _collateral(), policy)

    assert upside.projected_discounted_net_recovery > base.projected_discounted_net_recovery
    assert base.projected_discounted_net_recovery > downside.projected_discounted_net_recovery
    assert {item.policy_sha256 for item in (upside, base, downside)} == {policy.sha256}
    assert [item.scenario for item in (upside, base, downside)] == ["upside", "base", "downside"]


def test_unsecured_record_has_no_projected_collateral() -> None:
    result = project_collateral_recovery(
        _record(cashflows=(_cashflow("cash_collection", Decimal("20")),)),
        None,
        load_collateral_policy(POLICY_PATH),
    )

    assert result.collateral_type == "none"
    assert result.projected_discounted_net_recovery == 0
    assert result.combined_discounted_recovery == Decimal("20.00000000")


def test_rejects_collateral_that_does_not_match_contract() -> None:
    collateral = CollateralRecord(
        "COL-002",
        "OTHER",
        "real_estate",
        date(2026, 1, 1),
        Decimal("120"),
        Decimal("0.9"),
        "BRL",
    )

    with pytest.raises(DomainValidationError, match="does not match"):
        project_collateral_recovery(_record(), collateral, load_collateral_policy(POLICY_PATH))


def test_collateral_policy_rejects_schema_scenario_and_assumption_bounds(tmp_path: Path) -> None:
    document = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(document | {"schema_version": "2.0.0"}), encoding="utf-8")
    with pytest.raises(DomainValidationError, match="policy schema"):
        load_collateral_policy(path)

    document["sensitivities"].pop("upside")
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(DomainValidationError, match="requires upside"):
        load_collateral_policy(path)

    document = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    first = next(iter(document["assumptions"].values()))
    first["haircut"] = "2"
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(DomainValidationError, match="base assumptions"):
        load_collateral_policy(path)


def test_collateral_projection_rejects_unknown_and_effectively_invalid_assumptions() -> None:
    policy = load_collateral_policy(POLICY_PATH)
    with pytest.raises(DomainValidationError, match="unsupported"):
        project_collateral_recovery(
            _record(),
            replace(_collateral(), collateral_type="unsupported"),
            policy,
        )
    sensitivity = next(item for item in policy.sensitivities if item.scenario == "base")
    bad_rate = replace(sensitivity, haircut_delta=Decimal("2"))
    with pytest.raises(DomainValidationError, match="haircut or cost"):
        project_collateral_recovery(
            _record(), _collateral(), replace(policy, sensitivities=(bad_rate,))
        )
    base = next(item for item in policy.assumptions if item.collateral_type == "real_estate")
    bad_timing = replace(base, execution_months=0)
    with pytest.raises(DomainValidationError, match="timing or value change"):
        project_collateral_recovery(
            _record(),
            _collateral(),
            replace(
                policy,
                assumptions=(bad_timing,),
                sensitivities=(sensitivity,),
            ),
        )


def test_unsecured_record_rejects_observed_collateral_recovery() -> None:
    record = _record(cashflows=(_cashflow("collateral_execution", Decimal("10")),))
    with pytest.raises(DomainValidationError, match="has no collateral record"):
        project_collateral_recovery(record, None, load_collateral_policy(POLICY_PATH))
