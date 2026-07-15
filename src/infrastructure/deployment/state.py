"""Atomic application-release history and rollback planning."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from .environment import EnvironmentProfile


class DeploymentStateError(RuntimeError):
    """Raised when promotion or rollback preconditions are not met."""


@dataclass(frozen=True, slots=True)
class Release:
    image_tag: str
    commit: str
    recorded_at: str


class DeploymentStateStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"schema_version": 1, "environments": {}}
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != 1:
            raise DeploymentStateError("unsupported deployment state schema")
        return cast(dict[str, Any], payload)

    def _write(self, payload: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(f"{self.path.suffix}.tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(self.path)

    def plan(self, profile: EnvironmentProfile, image_tag: str, commit: str) -> dict[str, Any]:
        profile.validate_image_tag(image_tag)
        state = self._read()["environments"].get(profile.name, {})
        return {
            "environment": profile.name,
            "image_tag": image_tag,
            "commit": commit,
            "previous_release": state.get("current"),
            "database_migration_mode": profile.migration_mode,
            "database_rollback": "forward_only",
        }

    def promote(self, profile: EnvironmentProfile, image_tag: str, commit: str) -> dict[str, Any]:
        plan = self.plan(profile, image_tag, commit)
        payload = self._read()
        environments = payload["environments"]
        environment = environments.get(profile.name, {})
        releases = environment.get("releases", {})
        recorded_commit = releases.get(image_tag)
        if recorded_commit is not None and recorded_commit != commit:
            raise DeploymentStateError(
                f"immutable image tag {image_tag} is already associated with another commit"
            )
        current = environment.get("current")
        release = Release(image_tag, commit, datetime.now(UTC).isoformat())
        releases[image_tag] = commit
        environments[profile.name] = {
            "current": asdict(release),
            "previous": current,
            "releases": releases,
        }
        self._write(payload)
        return plan

    def rollback(self, profile: EnvironmentProfile) -> dict[str, Any]:
        payload = self._read()
        state = payload["environments"].get(profile.name)
        if not state or not state.get("previous"):
            raise DeploymentStateError(f"no previous {profile.name} release is available")
        current, previous = state["current"], state["previous"]
        payload["environments"][profile.name] = {
            "current": previous,
            "previous": current,
            "releases": state.get("releases", {}),
        }
        self._write(payload)
        return {
            "environment": profile.name,
            "restored": previous,
            "replaced": current,
            "database_rollback": "not_performed_forward_only",
        }
