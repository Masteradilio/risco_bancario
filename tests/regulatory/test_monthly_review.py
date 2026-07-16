from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from src.domain.exceptions import DomainValidationError, TemporalConsistencyError
from src.domain.staging import Stage
from src.regulatory.cmn4966 import InstrumentMonthlyReview, create_monthly_review_manifest


def _review(contract_id: str = "C-1") -> InstrumentMonthlyReview:
    return InstrumentMonthlyReview(
        contract_id,
        date(2026, 6, 30),
        date(2026, 7, 31),
        Stage.STAGE_1,
        Stage.STAGE_2,
        "10",
        "25",
        "SICR reassessment and updated lifetime ECL",
    )


def test_monthly_manifest_records_allowance_stage_and_hash() -> None:
    manifest = create_monthly_review_manifest(
        review_id="REV-2026-07",
        reference_date=date(2026, 7, 31),
        completed_at=datetime(2026, 8, 2, tzinfo=UTC),
        instruments=(_review(),),
    )
    assert manifest.total_previous_allowance == Decimal("10.00")
    assert manifest.total_current_allowance == Decimal("25.00")
    assert manifest.instruments[0].allowance_change == Decimal("15.00")
    assert manifest.stage_change_count == 1
    assert len(manifest.manifest_hash) == 64


def test_monthly_review_rejects_skipped_month_and_inconsistent_manifest() -> None:
    with pytest.raises(TemporalConsistencyError, match="cannot skip"):
        InstrumentMonthlyReview(
            "C-1",
            date(2026, 5, 31),
            date(2026, 7, 31),
            Stage.STAGE_1,
            Stage.STAGE_1,
            "10",
            "10",
            "Review",
        )
    with pytest.raises(DomainValidationError, match="duplicate"):
        create_monthly_review_manifest(
            review_id="REV",
            reference_date=date(2026, 7, 31),
            completed_at=datetime(2026, 8, 1, tzinfo=UTC),
            instruments=(_review(), _review()),
        )


def test_review_cannot_complete_before_reference_date() -> None:
    with pytest.raises(TemporalConsistencyError, match="before reference"):
        create_monthly_review_manifest(
            review_id="REV",
            reference_date=date(2026, 7, 31),
            completed_at=datetime(2026, 7, 30, tzinfo=UTC),
            instruments=(_review(),),
        )


def test_manifest_requires_instruments_with_matching_reference_date() -> None:
    with pytest.raises(DomainValidationError, match="requires instruments"):
        create_monthly_review_manifest(
            review_id="REV",
            reference_date=date(2026, 7, 31),
            completed_at=datetime(2026, 8, 1, tzinfo=UTC),
            instruments=(),
        )
    mismatched = InstrumentMonthlyReview(
        "C-2",
        date(2026, 7, 31),
        date(2026, 8, 31),
        Stage.STAGE_1,
        Stage.STAGE_1,
        "10",
        "10",
        "Review",
    )
    with pytest.raises(DomainValidationError, match="manifest reference date"):
        create_monthly_review_manifest(
            review_id="REV",
            reference_date=date(2026, 7, 31),
            completed_at=datetime(2026, 8, 1, tzinfo=UTC),
            instruments=(mismatched,),
        )
