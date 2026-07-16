import json
from datetime import date
from decimal import Decimal

import pytest

from src.domain.contracts import Contract
from src.domain.exceptions import DomainValidationError
from src.models.sicr import (
    OriginationBaselineLedger,
    create_origination_baseline,
    load_origination_ledger,
    save_origination_ledger,
)

POLICY_HASH = "a" * 64


def contract(months: int = 24) -> Contract:
    maturity_year = 2026 + months // 12
    maturity_month = months % 12 + 1
    if maturity_month > 12:
        maturity_year += 1
        maturity_month -= 12
    return Contract(
        "CT-ORIG",
        "CL-1",
        "CP-1",
        "personal_loan",
        date(2026, 1, 1),
        date(maturity_year, maturity_month, 1),
        "10000",
    )


def baseline(months: int = 24):
    return create_origination_baseline(
        contract(months),
        "0.08",
        "R2",
        model_name="logistic_12m_isotonic_frozen",
        model_version="0.2.0",
        policy_version="2026.07.1",
        policy_sha256=POLICY_HASH,
    )


def test_origination_baseline_persists_model_policy_and_original_term() -> None:
    result = baseline()
    assert result.recognition_date == date(2026, 1, 1)
    assert result.original_maturity_date == date(2028, 1, 1)
    assert result.pd_12m == Decimal("0.08000000")
    assert result.lifetime_pd_original_term > result.pd_12m
    assert result.model_version == "0.2.0"
    assert result.policy_sha256 == POLICY_HASH
    assert result.approval_status == "not_approved"


def test_short_original_term_limits_lifetime_pd() -> None:
    result = baseline(6)
    assert result.original_maturity_date == date(2026, 7, 1)
    assert result.lifetime_pd_original_term == result.pd_12m


def test_ledger_round_trip_is_deterministic(tmp_path) -> None:
    ledger = OriginationBaselineLedger("1.0.0", (baseline(),))
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    save_origination_ledger(first, ledger)
    loaded = load_origination_ledger(first)
    save_origination_ledger(second, loaded)
    assert loaded == ledger
    assert first.read_bytes() == second.read_bytes()


def test_tampered_persisted_baseline_is_rejected(tmp_path) -> None:
    path = tmp_path / "ledger.json"
    save_origination_ledger(path, OriginationBaselineLedger("1.0.0", (baseline(),)))
    document = json.loads(path.read_text(encoding="utf-8"))
    document["records"][0]["rating"] = "CHANGED"
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(DomainValidationError, match="hash mismatch"):
        load_origination_ledger(path)


def test_duplicate_contract_baselines_are_rejected() -> None:
    item = baseline()
    with pytest.raises(DomainValidationError, match="unique"):
        OriginationBaselineLedger("1.0.0", (item, item))


def test_origination_ledger_schema_and_policy_hash_fail_closed() -> None:
    with pytest.raises(DomainValidationError, match="unsupported origination ledger schema"):
        OriginationBaselineLedger("2.0.0", ())
    with pytest.raises(DomainValidationError, match="lowercase SHA-256"):
        create_origination_baseline(
            contract(),
            "0.08",
            "R2",
            model_name="model",
            model_version="1",
            policy_version="policy",
            policy_sha256="A" * 64,
        )


@pytest.mark.parametrize("field", ["model_name", "model_version", "policy_version"])
def test_required_origination_metadata_fails_closed(field) -> None:
    values = {
        "model_name": "model",
        "model_version": "1",
        "policy_version": "policy",
    }
    values[field] = " "
    with pytest.raises(DomainValidationError):
        create_origination_baseline(
            contract(),
            "0.08",
            "R2",
            policy_sha256=POLICY_HASH,
            **values,
        )
