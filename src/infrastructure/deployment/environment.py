"""Strict, secret-free environment profile loading."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

EnvironmentName = Literal["local", "test", "demo"]
MigrationMode = Literal["apply", "validate", "disabled"]
ReleaseTagPolicy = Literal["any", "semver"]
SEMVER = re.compile(r"^v?\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")


@dataclass(frozen=True, slots=True)
class EnvironmentProfile:
    name: EnvironmentName
    database_backend: Literal["sqlite", "postgresql"]
    migration_mode: MigrationMode
    release_tag_policy: ReleaseTagPolicy
    compose_profile: str

    def validate_image_tag(self, image_tag: str) -> None:
        if not image_tag or any(character.isspace() for character in image_tag):
            raise ValueError("image tag must be non-empty and contain no whitespace")
        if self.release_tag_policy == "semver" and not SEMVER.fullmatch(image_tag):
            raise ValueError(f"{self.name} requires a semantic version image tag")


def load_environment_profile(name: str, root: Path | None = None) -> EnvironmentProfile:
    if name not in {"local", "test", "demo"}:
        raise ValueError("environment must be local, test or demo")
    profiles_root = root or Path(__file__).resolve().parents[3] / "config/environments"
    payload = json.loads((profiles_root / f"{name}.json").read_text(encoding="utf-8"))
    forbidden = {key for key in payload if "secret" in key.lower() or "password" in key.lower()}
    if forbidden:
        raise ValueError("environment profiles must not contain secrets")
    if payload.get("schema_version") != 1 or payload.get("name") != name:
        raise ValueError("invalid environment profile identity or schema")
    profile = EnvironmentProfile(
        name=cast(EnvironmentName, name),
        database_backend=payload["database_backend"],
        migration_mode=payload["migration_mode"],
        release_tag_policy=payload["release_tag_policy"],
        compose_profile=payload["compose_profile"],
    )
    if profile.name == "demo" and profile.migration_mode != "validate":
        raise ValueError("demo must validate migrations at application startup")
    return profile
