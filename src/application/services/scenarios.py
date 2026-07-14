"""Governed scenario service and content-addressed external-source snapshots."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

from ...data.synthetic import generate_macroeconomic_bundle
from ...domain.exceptions import DomainValidationError
from ...domain.scenarios import (
    MacroTrajectoryPoint,
    MacroVariable,
    ScenarioApprovalStatus,
    ScenarioKind,
    ScenarioSet,
    ScenarioTrajectory,
)

POLICY_PATH = Path(__file__).resolve().parents[3] / "config" / "scenario_service" / "2026.07.1.json"
MACRO_FIELDS = (
    "gdp_growth",
    "inflation",
    "policy_rate",
    "unemployment",
    "household_debt",
    "risk_pressure",
)


def _canonical_json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


@dataclass(frozen=True, slots=True)
class ScenarioSourceSnapshot:
    provider: str
    source_version: str
    retrieved_at: datetime
    payload_hash: str
    payload: Mapping[str, Any]
    path: Path


class ScenarioSnapshotCache:
    """Store provider payloads before deterministic scenario calculations consume them."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def store(
        self,
        *,
        provider: str,
        source_version: str,
        retrieved_at: datetime,
        payload: Mapping[str, Any],
    ) -> ScenarioSourceSnapshot:
        if retrieved_at.tzinfo is None or retrieved_at.utcoffset() is None:
            raise DomainValidationError("retrieved_at must be timezone-aware")
        normalized_time = retrieved_at.astimezone(UTC)
        payload_hash = sha256(_canonical_json(payload)).hexdigest()
        document = {
            "metadata": {
                "provider": provider,
                "source_version": source_version,
                "retrieved_at": normalized_time.isoformat(),
                "payload_hash": payload_hash,
            },
            "payload": payload,
        }
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / f"{provider}-{source_version}-{payload_hash}.json"
        encoded = _canonical_json(document) + b"\n"
        if path.exists() and path.read_bytes() != encoded:
            raise DomainValidationError("content-addressed scenario snapshot collision")
        if not path.exists():
            path.write_bytes(encoded)
        return ScenarioSourceSnapshot(
            provider, source_version, normalized_time, payload_hash, payload, path
        )

    def load(self, path: Path) -> ScenarioSourceSnapshot:
        document = json.loads(path.read_bytes())
        metadata = document["metadata"]
        payload = document["payload"]
        actual_hash = sha256(_canonical_json(payload)).hexdigest()
        if actual_hash != metadata["payload_hash"]:
            raise DomainValidationError("scenario snapshot payload hash mismatch")
        retrieved_at = datetime.fromisoformat(metadata["retrieved_at"])
        if retrieved_at.tzinfo is None:
            raise DomainValidationError("scenario snapshot timestamp must be timezone-aware")
        return ScenarioSourceSnapshot(
            metadata["provider"],
            metadata["source_version"],
            retrieved_at.astimezone(UTC),
            actual_hash,
            payload,
            path,
        )


def load_scenario_set(*, seed: int = 20260714, policy_path: Path = POLICY_PATH) -> ScenarioSet:
    policy = json.loads(policy_path.read_bytes())
    metadata = policy["metadata"]
    bundle = generate_macroeconomic_bundle(seed=seed)
    if bundle.policy_version != policy["source"]["policy_version"]:
        raise DomainValidationError("scenario service source policy version mismatch")
    weights = dict(bundle.scenario_weights)
    trajectories: list[ScenarioTrajectory] = []
    for scenario_id in ("upside", "base", "downside", "stress"):
        observations = [item for item in bundle.scenarios if item.scenario_id == scenario_id]
        periods = tuple(
            MacroTrajectoryPoint(
                observation.reference_date,
                tuple(MacroVariable(field, getattr(observation, field)) for field in MACRO_FIELDS),
            )
            for observation in observations
        )
        trajectories.append(
            ScenarioTrajectory(
                scenario_id,
                policy["scenario_names"][scenario_id],
                ScenarioKind(scenario_id),
                weights[scenario_id],
                periods,
            )
        )
    status = ScenarioApprovalStatus(metadata["approval_status"])
    approval_date = (
        date.fromisoformat(metadata["approval_date"])
        if metadata["approval_date"] is not None
        else None
    )
    return ScenarioSet(
        trajectories[0].periods[0].reference_date,
        metadata["policy_version"],
        status,
        bundle.policy_hash,
        tuple(trajectories),
        metadata["approved_by"],
        approval_date,
    )
