"""Deterministic policy loading and content hashing."""

import json
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from .models import RiskPolicy


@dataclass(frozen=True, slots=True)
class LoadedRiskPolicy:
    policy: RiskPolicy
    configuration_hash: str
    source_path: Path


def load_risk_policy(path: str | Path) -> LoadedRiskPolicy:
    source_path = Path(path).resolve()
    raw = json.loads(source_path.read_text(encoding="utf-8"), parse_float=str)
    policy = RiskPolicy.model_validate(raw)
    canonical = json.dumps(raw, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    digest = sha256(canonical.encode("utf-8")).hexdigest()
    return LoadedRiskPolicy(policy=policy, configuration_hash=digest, source_path=source_path)
