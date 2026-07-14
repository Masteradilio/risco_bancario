"""Reconciled synthetic credit-risk disclosure package."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum
from hashlib import sha256

from ...domain.conventions import DecimalInput, money, non_empty
from ...domain.exceptions import DomainValidationError
from ...domain.staging import Stage
from ...ecl.calculation import ScenarioSensitivityReport
from ...ecl.overlays import ManagementOverlay


class AllowanceMovementType(StrEnum):
    ORIGINATION = "origination"
    ECL_REMEASUREMENT = "ecl_remeasurement"
    STAGE_TRANSFER = "stage_transfer"
    DERECOGNITION = "derecognition"
    WRITE_OFF = "write_off"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class DisclosureExposure:
    contract_id: str
    stage: Stage
    rating: str
    segment: str
    gross_exposure: DecimalInput
    allowance: DecimalInput

    def __post_init__(self) -> None:
        for field in ("contract_id", "rating", "segment"):
            object.__setattr__(self, field, non_empty(getattr(self, field), field=field))
        gross = money(self.gross_exposure, field="gross_exposure")
        allowance = money(self.allowance, field="allowance")
        if allowance > gross:
            raise DomainValidationError("allowance cannot exceed gross exposure")
        object.__setattr__(self, "gross_exposure", gross)
        object.__setattr__(self, "allowance", allowance)


@dataclass(frozen=True, slots=True)
class AllowanceMovement:
    movement_id: str
    movement_type: AllowanceMovementType
    amount: DecimalInput
    stage: Stage | None = None
    from_stage: Stage | None = None
    to_stage: Stage | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "movement_id", non_empty(self.movement_id, field="movement_id"))
        amount = money(self.amount, field="movement_amount", allow_negative=True)
        if self.movement_type == AllowanceMovementType.STAGE_TRANSFER:
            if self.stage is not None or self.from_stage is None or self.to_stage is None:
                raise DomainValidationError("stage transfer requires from_stage and to_stage only")
            if self.from_stage == self.to_stage or amount <= 0:
                raise DomainValidationError(
                    "stage transfer requires different stages and positive amount"
                )
        elif self.stage is None or self.from_stage is not None or self.to_stage is not None:
            raise DomainValidationError("non-transfer movement requires stage only")
        object.__setattr__(self, "amount", amount)


@dataclass(frozen=True, slots=True)
class StageAllowanceReconciliation:
    stage: Stage
    opening_allowance: Decimal
    net_movements: Decimal
    closing_allowance: Decimal
    difference: Decimal


@dataclass(frozen=True, slots=True)
class StageTransferSummary:
    from_stage: Stage
    to_stage: Stage
    amount: Decimal


@dataclass(frozen=True, slots=True)
class ExposureSummary:
    dimension: str
    value: str
    contract_count: int
    gross_exposure: Decimal
    allowance: Decimal


@dataclass(frozen=True, slots=True)
class SensitivityDisclosure:
    case_id: str
    kind: str
    ecl: Decimal
    delta_from_base: Decimal


@dataclass(frozen=True, slots=True)
class OverlayDisclosure:
    overlay_id: str
    amount: Decimal
    reason: str
    version: str
    active: bool


@dataclass(frozen=True, slots=True)
class RegimeBoundary:
    accounting_ecl: str = "IFRS9_accounting_ECL_with_applicable_CMN4966_or_BCB352_rules"
    local_floor: str = "BCB352_minimum_provision_separate_from_accounting_ECL"
    capital_irb_in_scope: bool = False
    downturn_lgd_accepted_as_accounting_lgd: bool = False


@dataclass(frozen=True, slots=True)
class SyntheticDisclosurePackage:
    reference_date: date
    data_classification: str
    stage_reconciliation: tuple[StageAllowanceReconciliation, ...]
    movement_totals: tuple[tuple[str, Decimal], ...]
    stage_transfers: tuple[StageTransferSummary, ...]
    exposure_by_rating: tuple[ExposureSummary, ...]
    exposure_by_segment: tuple[ExposureSummary, ...]
    base_ecl: Decimal
    stress_ecl: Decimal
    sensitivities: tuple[SensitivityDisclosure, ...]
    overlays: tuple[OverlayDisclosure, ...]
    regime_boundary: RegimeBoundary
    source_locator: str
    package_hash: str


def _sum(values: tuple[Decimal, ...]) -> Decimal:
    return sum(values, Decimal("0")).quantize(Decimal("0.01"))


def _unique_exposures(exposures: tuple[DisclosureExposure, ...], label: str) -> None:
    ids = [item.contract_id for item in exposures]
    if len(ids) != len(set(ids)):
        raise DomainValidationError(f"{label} exposures contain duplicate contracts")


def _movement_by_stage(movement: AllowanceMovement, stage: Stage) -> Decimal:
    amount = Decimal(movement.amount)
    if movement.movement_type != AllowanceMovementType.STAGE_TRANSFER:
        return amount if movement.stage == stage else Decimal("0")
    if movement.from_stage == stage:
        return -amount
    if movement.to_stage == stage:
        return amount
    return Decimal("0")


def _summarize_exposure(
    exposures: tuple[DisclosureExposure, ...], attribute: str
) -> tuple[ExposureSummary, ...]:
    values = sorted({str(getattr(item, attribute)) for item in exposures})
    return tuple(
        ExposureSummary(
            attribute,
            value,
            len(
                group := tuple(item for item in exposures if str(getattr(item, attribute)) == value)
            ),
            _sum(tuple(Decimal(item.gross_exposure) for item in group)),
            _sum(tuple(Decimal(item.allowance) for item in group)),
        )
        for value in values
    )


def generate_synthetic_disclosure_package(
    *,
    reference_date: date,
    opening_exposures: tuple[DisclosureExposure, ...],
    closing_exposures: tuple[DisclosureExposure, ...],
    movements: tuple[AllowanceMovement, ...],
    sensitivity_report: ScenarioSensitivityReport,
    overlays: tuple[ManagementOverlay, ...],
) -> SyntheticDisclosurePackage:
    if not opening_exposures or not closing_exposures:
        raise DomainValidationError("disclosure package requires opening and closing exposures")
    _unique_exposures(opening_exposures, "opening")
    _unique_exposures(closing_exposures, "closing")
    movement_ids = [item.movement_id for item in movements]
    if len(movement_ids) != len(set(movement_ids)):
        raise DomainValidationError("allowance movement ids must be unique")
    overlay_ids = [item.overlay_id for item in overlays]
    if len(overlay_ids) != len(set(overlay_ids)):
        raise DomainValidationError("overlay ids must be unique")
    reconciliations: list[StageAllowanceReconciliation] = []
    for stage in Stage:
        opening = _sum(
            tuple(Decimal(item.allowance) for item in opening_exposures if item.stage == stage)
        )
        closing = _sum(
            tuple(Decimal(item.allowance) for item in closing_exposures if item.stage == stage)
        )
        net = _sum(tuple(_movement_by_stage(item, stage) for item in movements))
        difference = (opening + net - closing).quantize(Decimal("0.01"))
        reconciliations.append(
            StageAllowanceReconciliation(stage, opening, net, closing, difference)
        )
    if any(item.difference != 0 for item in reconciliations):
        raise DomainValidationError(
            "allowance movements do not reconcile opening to closing by stage"
        )
    movement_totals = tuple(
        (
            movement_type.value,
            _sum(
                tuple(
                    Decimal(item.amount)
                    for item in movements
                    if item.movement_type == movement_type
                )
            ),
        )
        for movement_type in AllowanceMovementType
    )
    transfer_key_set: set[tuple[Stage, Stage]] = set()
    for item in movements:
        if item.movement_type == AllowanceMovementType.STAGE_TRANSFER:
            assert item.from_stage is not None and item.to_stage is not None
            transfer_key_set.add((item.from_stage, item.to_stage))
    transfer_keys = sorted(transfer_key_set, key=lambda pair: (int(pair[0]), int(pair[1])))
    transfers = tuple(
        StageTransferSummary(
            from_stage,
            to_stage,
            _sum(
                tuple(
                    Decimal(item.amount)
                    for item in movements
                    if item.from_stage == from_stage and item.to_stage == to_stage
                )
            ),
        )
        for from_stage, to_stage in transfer_keys
    )
    sensitivities = tuple(
        SensitivityDisclosure(
            item.case_id, item.kind, item.probability_weighted_ecl, item.delta_from_base
        )
        for item in sensitivity_report.results
    )
    overlay_rows = tuple(
        OverlayDisclosure(
            item.overlay_id,
            Decimal(item.amount),
            item.reason,
            item.version,
            item.is_active(reference_date),
        )
        for item in overlays
    )
    payload = {
        "reference_date": reference_date,
        "stage_reconciliation": [asdict(item) for item in reconciliations],
        "movement_totals": movement_totals,
        "stage_transfers": [asdict(item) for item in transfers],
        "closing_exposures": [asdict(item) for item in closing_exposures],
        "sensitivities": [asdict(item) for item in sensitivities],
        "overlays": [asdict(item) for item in overlay_rows],
    }
    package_hash = sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()
    return SyntheticDisclosurePackage(
        reference_date,
        "synthetic_demonstrative_not_financial_statements",
        tuple(reconciliations),
        movement_totals,
        transfers,
        _summarize_exposure(closing_exposures, "rating"),
        _summarize_exposure(closing_exposures, "segment"),
        sensitivity_report.base_ecl,
        sensitivity_report.stress_ecl,
        sensitivities,
        overlay_rows,
        RegimeBoundary(),
        "Resolução CMN nº 4.966/2021, arts. 65-66",
        package_hash,
    )
