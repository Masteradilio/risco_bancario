from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from src.domain.exceptions import DomainValidationError
from src.domain.staging import Stage
from src.ecl.calculation import ScenarioSensitivityReport, SensitivityResult
from src.ecl.overlays import ManagementOverlay
from src.regulatory.cmn4966 import (
    AllowanceMovement,
    AllowanceMovementType,
    DisclosureExposure,
    generate_synthetic_disclosure_package,
)


def _sensitivity() -> ScenarioSensitivityReport:
    return ScenarioSensitivityReport(
        Decimal("180"),
        Decimal("260"),
        Decimal("80"),
        (
            SensitivityResult("downside_weight", "weight", Decimal("210"), Decimal("30")),
            SensitivityResult("unemployment", "trajectory", Decimal("225"), Decimal("45")),
        ),
        "2026.07.1",
        "a" * 64,
    )


def _overlay() -> ManagementOverlay:
    return ManagementOverlay(
        "OV-1",
        "15",
        "Emerging concentration not captured by the model",
        "Risk Committee",
        datetime(2026, 6, 30, tzinfo=UTC),
        date(2026, 7, 1),
        date(2026, 12, 31),
        "1.0",
    )


def _opening() -> tuple[DisclosureExposure, ...]:
    return (
        DisclosureExposure("C-1", Stage.STAGE_1, "A", "retail", "1000", "100"),
        DisclosureExposure("C-2", Stage.STAGE_2, "C", "sme", "500", "80"),
    )


def _closing() -> tuple[DisclosureExposure, ...]:
    return (
        DisclosureExposure("C-1", Stage.STAGE_2, "B", "retail", "950", "150"),
        DisclosureExposure("C-2", Stage.STAGE_2, "C", "sme", "450", "70"),
        DisclosureExposure("C-3", Stage.STAGE_1, "A", "retail", "200", "20"),
    )


def _movements() -> tuple[AllowanceMovement, ...]:
    return (
        AllowanceMovement(
            "M-1",
            AllowanceMovementType.STAGE_TRANSFER,
            "100",
            from_stage=Stage.STAGE_1,
            to_stage=Stage.STAGE_2,
        ),
        AllowanceMovement("M-2", AllowanceMovementType.ECL_REMEASUREMENT, "50", Stage.STAGE_2),
        AllowanceMovement("M-3", AllowanceMovementType.DERECOGNITION, "-10", Stage.STAGE_2),
        AllowanceMovement("M-4", AllowanceMovementType.ORIGINATION, "20", Stage.STAGE_1),
    )


def test_synthetic_disclosure_package_reconciles_every_stage() -> None:
    package = generate_synthetic_disclosure_package(
        reference_date=date(2026, 7, 31),
        opening_exposures=_opening(),
        closing_exposures=_closing(),
        movements=_movements(),
        sensitivity_report=_sensitivity(),
        overlays=(_overlay(),),
    )
    assert all(row.difference == 0 for row in package.stage_reconciliation)
    assert package.stage_reconciliation[0].closing_allowance == Decimal("20.00")
    assert package.stage_reconciliation[1].closing_allowance == Decimal("220.00")
    assert package.stage_transfers[0].amount == Decimal("100.00")
    assert len(package.package_hash) == 64


def test_exposure_rating_segment_sensitivity_and_overlay_are_included() -> None:
    package = generate_synthetic_disclosure_package(
        reference_date=date(2026, 7, 31),
        opening_exposures=_opening(),
        closing_exposures=_closing(),
        movements=_movements(),
        sensitivity_report=_sensitivity(),
        overlays=(_overlay(),),
    )
    retail = next(item for item in package.exposure_by_segment if item.value == "retail")
    rating_a = next(item for item in package.exposure_by_rating if item.value == "A")
    assert retail.contract_count == 2
    assert retail.gross_exposure == Decimal("1150.00")
    assert rating_a.allowance == Decimal("20.00")
    assert package.sensitivities[0].delta_from_base == Decimal("30")
    assert package.overlays[0].active
    assert package.data_classification.startswith("synthetic_demonstrative")
    assert not package.regime_boundary.capital_irb_in_scope
    assert not package.regime_boundary.downturn_lgd_accepted_as_accounting_lgd
    assert "separate" in package.regime_boundary.local_floor


def test_unreconciled_movements_fail_closed() -> None:
    with pytest.raises(DomainValidationError, match="do not reconcile"):
        generate_synthetic_disclosure_package(
            reference_date=date(2026, 7, 31),
            opening_exposures=_opening(),
            closing_exposures=_closing(),
            movements=_movements()[:-1],
            sensitivity_report=_sensitivity(),
            overlays=(),
        )


def test_duplicate_contracts_or_movements_and_invalid_transfer_fail_closed() -> None:
    with pytest.raises(DomainValidationError, match="duplicate contracts"):
        generate_synthetic_disclosure_package(
            reference_date=date(2026, 7, 31),
            opening_exposures=_opening() + (_opening()[0],),
            closing_exposures=_closing(),
            movements=_movements(),
            sensitivity_report=_sensitivity(),
            overlays=(),
        )
    with pytest.raises(DomainValidationError, match="different stages"):
        AllowanceMovement(
            "BAD",
            AllowanceMovementType.STAGE_TRANSFER,
            "10",
            from_stage=Stage.STAGE_1,
            to_stage=Stage.STAGE_1,
        )


def test_disclosure_input_invariants_fail_closed() -> None:
    with pytest.raises(DomainValidationError, match="cannot exceed"):
        DisclosureExposure("C", Stage.STAGE_1, "A", "retail", "10", "11")
    with pytest.raises(DomainValidationError, match="from_stage and to_stage only"):
        AllowanceMovement(
            "BAD-TRANSFER",
            AllowanceMovementType.STAGE_TRANSFER,
            "10",
            stage=Stage.STAGE_1,
        )
    with pytest.raises(DomainValidationError, match="requires stage only"):
        AllowanceMovement("BAD-MOVEMENT", AllowanceMovementType.OTHER, "1")
    with pytest.raises(DomainValidationError, match="requires opening and closing"):
        generate_synthetic_disclosure_package(
            reference_date=date(2026, 7, 31),
            opening_exposures=(),
            closing_exposures=_closing(),
            movements=(),
            sensitivity_report=_sensitivity(),
            overlays=(),
        )


def test_duplicate_movement_and_overlay_ids_fail_closed() -> None:
    duplicate_movement = _movements() + (_movements()[0],)
    with pytest.raises(DomainValidationError, match="movement ids"):
        generate_synthetic_disclosure_package(
            reference_date=date(2026, 7, 31),
            opening_exposures=_opening(),
            closing_exposures=_closing(),
            movements=duplicate_movement,
            sensitivity_report=_sensitivity(),
            overlays=(),
        )
    with pytest.raises(DomainValidationError, match="overlay ids"):
        generate_synthetic_disclosure_package(
            reference_date=date(2026, 7, 31),
            opening_exposures=_opening(),
            closing_exposures=_closing(),
            movements=_movements(),
            sensitivity_report=_sensitivity(),
            overlays=(_overlay(), _overlay()),
        )


def test_corrupted_transfer_is_rejected_by_package_boundary() -> None:
    transfer = _movements()[0]
    object.__setattr__(transfer, "from_stage", None)
    object.__setattr__(transfer, "to_stage", None)
    with pytest.raises(DomainValidationError, match="origin and destination"):
        generate_synthetic_disclosure_package(
            reference_date=date(2026, 7, 31),
            opening_exposures=_opening(),
            closing_exposures=_opening(),
            movements=(transfer,),
            sensitivity_report=_sensitivity(),
            overlays=(),
        )
