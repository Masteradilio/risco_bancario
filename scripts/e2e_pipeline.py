"""Execute the canonical synthetic end-to-end demonstration journey."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

from src.application.e2e import run_e2e_journey

ROOT = Path(__file__).resolve().parents[1]
COMMIT_PATTERN = re.compile(r"[0-9a-f]{7,40}")


def _source_fingerprint(root: Path) -> str:
    """Fingerprint a source archive when Git metadata is intentionally absent."""
    digest = hashlib.sha256()
    candidates = [path for path in (root / "pyproject.toml",) if path.is_file()]
    for directory in (root / "src", root / "config", root / "scripts"):
        if directory.is_dir():
            candidates.extend(path for path in directory.rglob("*") if path.is_file())
    for path in sorted(candidates, key=lambda item: item.as_posix()):
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()[:12]


def resolve_code_version(explicit: str | None, root: Path = ROOT) -> str:
    """Resolve a Git commit or deterministic archive fingerprint."""
    if explicit is not None:
        if not COMMIT_PATTERN.fullmatch(explicit):
            raise ValueError("--commit must be 7 to 40 lowercase hexadecimal characters")
        return explicit
    result = subprocess.run(
        ["git", "rev-parse", "--short=12", "HEAD"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    candidate = result.stdout.strip()
    return (
        candidate
        if result.returncode == 0 and COMMIT_PATTERN.fullmatch(candidate)
        else _source_fingerprint(root)
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("evidence/e2e"))
    parser.add_argument("--commit", default=None)
    args = parser.parse_args()
    commit = resolve_code_version(args.commit)
    with tempfile.TemporaryDirectory(prefix="risco-e2e-") as directory:
        report = run_e2e_journey(args.output, Path(directory), commit)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
