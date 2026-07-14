"""Versioned persistence contract for origination risk baselines."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

from ...domain.contracts import Contract
from ...domain.conventions import DecimalInput, non_empty, rate
from ...domain.exceptions import DomainValidationError
from ..pd import project_pd_term_structure

LEDGER_SCHEMA_VERSION = "1.0.0"


@dataclass(frozen=True, slots=True)
class OriginationRiskBaseline:
    contract_id: str
    recognition_date: date
    original_maturity_date: date
    pd_12m: Decimal
    rating: str
    lifetime_pd_original_term: Decimal
    model_name: str
    model_version: str
    policy_version: str
    policy_sha256: str
    approval_status: str
    record_sha256: str


@dataclass(frozen=True, slots=True)
class OriginationBaselineLedger:
    schema_version: str
    records: tuple[OriginationRiskBaseline, ...]

    def __post_init__(self) -> None:
        if self.schema_version != LEDGER_SCHEMA_VERSION:
            raise DomainValidationError("unsupported origination ledger schema")
        ids = [item.contract_id for item in self.records]
        if len(ids) != len(set(ids)):
            raise DomainValidationError("origination ledger contract_id must be unique")


def _payload(record: OriginationRiskBaseline) -> dict[str, str]:
    return {
        "contract_id": record.contract_id,
        "recognition_date": record.recognition_date.isoformat(),
        "original_maturity_date": record.original_maturity_date.isoformat(),
        "pd_12m": str(record.pd_12m),
        "rating": record.rating,
        "lifetime_pd_original_term": str(record.lifetime_pd_original_term),
        "model_name": record.model_name,
        "model_version": record.model_version,
        "policy_version": record.policy_version,
        "policy_sha256": record.policy_sha256,
        "approval_status": record.approval_status,
    }


def _hash(payload: dict[str, str]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(canonical.encode()).hexdigest()


def create_origination_baseline(
    contract: Contract,
    pd_12m: DecimalInput,
    rating: str,
    *,
    model_name: str,
    model_version: str,
    policy_version: str,
    policy_sha256: str,
    approval_status: str = "not_approved",
) -> OriginationRiskBaseline:
    probability = rate(pd_12m, field="pd_12m")
    metadata = {
        "rating": rating,
        "model_name": model_name,
        "model_version": model_version,
        "policy_version": policy_version,
        "approval_status": approval_status,
    }
    normalized = {key: non_empty(value, field=key) for key, value in metadata.items()}
    if len(policy_sha256) != 64 or any(
        character not in "0123456789abcdef" for character in policy_sha256
    ):
        raise DomainValidationError("policy_sha256 must be a lowercase SHA-256 hex digest")
    curve = project_pd_term_structure(
        contract.contract_id,
        contract.origination_date,
        contract.maturity_date,
        float(probability),
    )
    lifetime = Decimal(str(curve.lifetime_pd)).quantize(Decimal("0.00000001"))
    draft = OriginationRiskBaseline(
        contract.contract_id,
        contract.origination_date,
        contract.maturity_date,
        probability,
        normalized["rating"],
        lifetime,
        normalized["model_name"],
        normalized["model_version"],
        normalized["policy_version"],
        policy_sha256,
        normalized["approval_status"],
        "",
    )
    return OriginationRiskBaseline(**{**asdict(draft), "record_sha256": _hash(_payload(draft))})


def save_origination_ledger(path: Path, ledger: OriginationBaselineLedger) -> None:
    rows = [{**_payload(item), "record_sha256": item.record_sha256} for item in ledger.records]
    document = {"schema_version": ledger.schema_version, "records": rows}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def load_origination_ledger(path: Path) -> OriginationBaselineLedger:
    document = json.loads(path.read_text(encoding="utf-8"))
    records: list[OriginationRiskBaseline] = []
    for raw in document["records"]:
        supplied_hash = raw.pop("record_sha256")
        if _hash(raw) != supplied_hash:
            raise DomainValidationError("origination baseline hash mismatch")
        records.append(
            OriginationRiskBaseline(
                raw["contract_id"],
                date.fromisoformat(raw["recognition_date"]),
                date.fromisoformat(raw["original_maturity_date"]),
                Decimal(raw["pd_12m"]),
                raw["rating"],
                Decimal(raw["lifetime_pd_original_term"]),
                raw["model_name"],
                raw["model_version"],
                raw["policy_version"],
                raw["policy_sha256"],
                raw["approval_status"],
                supplied_hash,
            )
        )
    return OriginationBaselineLedger(document["schema_version"], tuple(records))
