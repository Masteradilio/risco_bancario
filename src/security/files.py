"""Fail-closed validation for uploads and private storage for generated exports."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4
from xml.etree import ElementTree


class FileSecurityError(ValueError):
    """Raised when external file content or an export path violates policy."""


@dataclass(frozen=True, slots=True)
class UploadPolicy:
    max_bytes: int = 5 * 1024 * 1024
    allowed_content_types: tuple[tuple[str, tuple[str, ...]], ...] = (
        (".csv", ("text/csv", "application/csv")),
        (".json", ("application/json",)),
        (".xml", ("application/xml", "text/xml")),
    )

    def __post_init__(self) -> None:
        if self.max_bytes <= 0:
            raise ValueError("upload maximum size must be positive")


@dataclass(frozen=True, slots=True)
class ValidatedUpload:
    filename: str
    content_type: str
    size_bytes: int
    sha256: str
    content: bytes


@dataclass(frozen=True, slots=True)
class ExportArtifact:
    artifact_id: str
    filename: str
    path: Path
    size_bytes: int
    sha256: str


def _safe_filename(filename: str) -> str:
    if (
        not filename
        or Path(filename).name != filename
        or "/" in filename
        or "\\" in filename
        or "\x00" in filename
        or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,199}", filename)
    ):
        raise FileSecurityError("unsafe filename")
    return filename


def validate_upload(
    filename: str,
    content_type: str,
    content: bytes,
    policy: UploadPolicy | None = None,
) -> ValidatedUpload:
    """Validate metadata, size, encoding and structure before content is consumed."""
    policy = policy or UploadPolicy()
    filename = _safe_filename(filename)
    if not content or len(content) > policy.max_bytes:
        raise FileSecurityError("upload is empty or exceeds the maximum size")
    suffix = Path(filename).suffix.lower()
    allowed = dict(policy.allowed_content_types)
    if suffix not in allowed or content_type.lower() not in allowed[suffix]:
        raise FileSecurityError("file extension or content type is not allowed")
    if b"\x00" in content:
        raise FileSecurityError("binary content is not allowed")
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise FileSecurityError("upload must be valid UTF-8") from exc

    try:
        if suffix == ".json":
            json.loads(text)
        elif suffix == ".csv":
            rows = csv.reader(io.StringIO(text))
            if next(rows, None) is None:
                raise FileSecurityError("CSV must contain at least one row")
        else:
            lowered = text.lower()
            if "<!doctype" in lowered or "<!entity" in lowered:
                raise FileSecurityError("XML DTD and entities are forbidden")
            ElementTree.fromstring(text)  # noqa: S314 - DTD/entities rejected above
    except (csv.Error, json.JSONDecodeError, ElementTree.ParseError) as exc:
        raise FileSecurityError("upload structure is invalid") from exc

    return ValidatedUpload(
        filename=filename,
        content_type=content_type.lower(),
        size_bytes=len(content),
        sha256=hashlib.sha256(content).hexdigest(),
        content=content,
    )


class SecureExportStore:
    """Write generated exports under server-generated names and private permissions."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.root, 0o700)

    def write(self, filename: str, content: bytes) -> ExportArtifact:
        filename = _safe_filename(filename)
        if not content:
            raise FileSecurityError("empty exports are forbidden")
        artifact_id = uuid4().hex
        stored_name = f"{artifact_id}-{filename}"
        path = (self.root / stored_name).resolve()
        if path.parent != self.root:
            raise FileSecurityError("export path escapes the private root")
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(descriptor, "wb") as target:
                target.write(content)
        except BaseException:
            path.unlink(missing_ok=True)
            raise
        os.chmod(path, 0o600)
        return ExportArtifact(
            artifact_id=artifact_id,
            filename=filename,
            path=path,
            size_bytes=len(content),
            sha256=hashlib.sha256(content).hexdigest(),
        )

    def purge_older_than(self, cutoff: datetime) -> int:
        cutoff_utc = cutoff.astimezone(UTC)
        deleted = 0
        for path in self.root.iterdir():
            if not path.is_file() or not re.fullmatch(r"[0-9a-f]{32}-.+", path.name):
                continue
            modified = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
            if modified < cutoff_utc:
                path.unlink()
                deleted += 1
        return deleted
