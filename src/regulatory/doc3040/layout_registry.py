"""Reference-date registry and provenance guards for Document 3040 layouts."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from ...domain.exceptions import DomainValidationError

DEFAULT_REGISTRY_DIR = Path("config/regulatory/doc3040/layouts")
_SHA256 = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True, slots=True)
class ArtifactRef:
    name: str
    filename: str
    url: str
    sha256: str


@dataclass(frozen=True, slots=True)
class XsdRef:
    document_code: str
    filename: str
    source_url: str
    sha256: str


@dataclass(frozen=True, slots=True)
class DomainCatalogRef:
    artifact: str
    sheets: tuple[str, ...]
    active_markers: tuple[str, ...]
    future_markers_must_be_filtered: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CriticCatalogRef:
    artifacts: tuple[str, ...]
    critics_last_update: date
    execution_status: str


@dataclass(frozen=True, slots=True)
class LayoutVersion:
    document_code: str
    version: str
    effective_from: date
    effective_to: date
    observed_at: date
    source_id: str
    normative_acts: tuple[str, ...]
    artifacts: Mapping[str, ArtifactRef]
    domain_catalog: DomainCatalogRef
    critic_catalog: CriticCatalogRef
    xsd: XsdRef | None
    xsd_status: str
    generation_enabled: bool
    manifest_path: Path

    def artifact(self, name: str) -> ArtifactRef:
        try:
            return self.artifacts[name]
        except KeyError as exc:
            raise DomainValidationError(
                f"layout {self.version} does not declare artifact {name}"
            ) from exc

    def require_official_xsd(self) -> XsdRef:
        if self.xsd is None:
            raise DomainValidationError(
                f"layout {self.version} cannot enable XSD validation: {self.xsd_status}"
            )
        if self.xsd.document_code != self.document_code:
            raise DomainValidationError(
                f"XSD document {self.xsd.document_code} cannot validate "
                f"document {self.document_code}"
            )
        return self.xsd


def _required_text(payload: Mapping[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value or value != value.strip():
        raise DomainValidationError(f"layout manifest field {field} must be non-empty")
    return value


def _iso_date(payload: Mapping[str, Any], field: str) -> date:
    try:
        return date.fromisoformat(_required_text(payload, field))
    except ValueError as exc:
        raise DomainValidationError(f"layout manifest field {field} must be ISO date") from exc


def _hash(value: str, field: str) -> str:
    normalized = value.lower()
    if not _SHA256.fullmatch(normalized):
        raise DomainValidationError(f"{field} must be a lowercase SHA-256")
    return normalized


def _tuple_of_text(payload: Mapping[str, Any], field: str) -> tuple[str, ...]:
    value = payload.get(field)
    if not isinstance(value, list) or not value or not all(isinstance(x, str) and x for x in value):
        raise DomainValidationError(f"layout manifest field {field} must be a non-empty list")
    return tuple(value)


def load_layout_manifest(path: Path) -> LayoutVersion:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise DomainValidationError("layout manifest root must be an object")
    artifacts_payload = payload.get("artifacts")
    if not isinstance(artifacts_payload, dict) or not artifacts_payload:
        raise DomainValidationError("layout manifest requires official artifacts")
    artifacts: dict[str, ArtifactRef] = {}
    for name, raw in artifacts_payload.items():
        if not isinstance(raw, dict):
            raise DomainValidationError(f"artifact {name} must be an object")
        url = _required_text(raw, "url")
        if not url.startswith("https://www.bcb.gov.br/"):
            raise DomainValidationError(f"artifact {name} must use an official BCB URL")
        artifacts[name] = ArtifactRef(
            name=name,
            filename=_required_text(raw, "filename"),
            url=url,
            sha256=_hash(_required_text(raw, "sha256"), f"artifact {name} sha256"),
        )
    domains = payload.get("domain_catalog")
    critics = payload.get("critic_catalog")
    if not isinstance(domains, dict) or not isinstance(critics, dict):
        raise DomainValidationError("layout manifest requires domain and critic catalogs")
    domain_ref = DomainCatalogRef(
        artifact=_required_text(domains, "artifact"),
        sheets=_tuple_of_text(domains, "sheets"),
        active_markers=_tuple_of_text(domains, "active_markers"),
        future_markers_must_be_filtered=_tuple_of_text(domains, "future_markers_must_be_filtered"),
    )
    critic_ref = CriticCatalogRef(
        artifacts=_tuple_of_text(critics, "artifacts"),
        critics_last_update=_iso_date(critics, "critics_last_update"),
        execution_status=_required_text(critics, "execution_status"),
    )
    for artifact_name in (domain_ref.artifact, *critic_ref.artifacts):
        if artifact_name not in artifacts:
            raise DomainValidationError(f"catalog references unknown artifact {artifact_name}")
    xsd_payload = payload.get("xsd")
    xsd = None
    if xsd_payload is not None:
        if not isinstance(xsd_payload, dict):
            raise DomainValidationError("xsd must be an object or null")
        source_url = _required_text(xsd_payload, "source_url")
        if not source_url.startswith("https://www.bcb.gov.br/"):
            raise DomainValidationError("XSD provenance must use an official BCB URL")
        xsd = XsdRef(
            document_code=_required_text(xsd_payload, "document_code"),
            filename=_required_text(xsd_payload, "filename"),
            source_url=source_url,
            sha256=_hash(_required_text(xsd_payload, "sha256"), "xsd sha256"),
        )
    layout = LayoutVersion(
        document_code=_required_text(payload, "document_code"),
        version=_required_text(payload, "version"),
        effective_from=_iso_date(payload, "effective_from"),
        effective_to=_iso_date(payload, "effective_to"),
        observed_at=_iso_date(payload, "observed_at"),
        source_id=_required_text(payload, "source_id"),
        normative_acts=_tuple_of_text(payload, "normative_acts"),
        artifacts=artifacts,
        domain_catalog=domain_ref,
        critic_catalog=critic_ref,
        xsd=xsd,
        xsd_status=_required_text(payload, "xsd_status"),
        generation_enabled=payload.get("generation_enabled") is True,
        manifest_path=path,
    )
    if layout.document_code != "3040":
        raise DomainValidationError("layout registry accepts only document 3040")
    if layout.effective_from.day != 1 or layout.effective_to.day != 1:
        raise DomainValidationError(
            "layout effective bounds must start on the first day of a month"
        )
    if layout.effective_from >= layout.effective_to:
        raise DomainValidationError("layout effective_from must precede effective_to")
    if layout.generation_enabled and layout.xsd is None:
        raise DomainValidationError("generation cannot be enabled without a provenanced 3040 XSD")
    return layout


def load_layout_registry(directory: Path = DEFAULT_REGISTRY_DIR) -> tuple[LayoutVersion, ...]:
    paths = sorted(directory.glob("*.json"))
    if not paths:
        raise DomainValidationError(f"no Doc3040 layout manifests found in {directory}")
    layouts = tuple(
        sorted((load_layout_manifest(path) for path in paths), key=lambda x: x.effective_from)
    )
    versions = [layout.version for layout in layouts]
    if len(versions) != len(set(versions)):
        raise DomainValidationError("Doc3040 layout versions must be unique")
    for previous, current in zip(layouts, layouts[1:], strict=False):
        if current.effective_from < previous.effective_to:
            raise DomainValidationError("Doc3040 layout effective ranges must not overlap")
    return layouts


def layout_for_reference_month(
    reference_month: date, layouts: tuple[LayoutVersion, ...] | None = None
) -> LayoutVersion:
    if reference_month.day != 1:
        raise DomainValidationError("Doc3040 reference_month must be the first day of its month")
    registry = layouts or load_layout_registry()
    matches = [
        layout
        for layout in registry
        if layout.effective_from <= reference_month < layout.effective_to
    ]
    if len(matches) != 1:
        raise DomainValidationError(
            f"unsupported Doc3040 reference month {reference_month:%Y-%m}; "
            "no unique observed layout version is registered"
        )
    return matches[0]


def verify_artifact_file(artifact: ArtifactRef, path: Path) -> None:
    if path.name != artifact.filename:
        raise DomainValidationError(
            f"artifact filename mismatch: expected {artifact.filename}, received {path.name}"
        )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != artifact.sha256:
        raise DomainValidationError(f"artifact {artifact.name} SHA-256 mismatch")


def load_official_xsd(layout: LayoutVersion, path: Path) -> bytes:
    xsd = layout.require_official_xsd()
    artifact = ArtifactRef("xsd", xsd.filename, xsd.source_url, xsd.sha256)
    verify_artifact_file(artifact, path)
    return path.read_bytes()
