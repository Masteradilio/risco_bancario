"""Execute the canonical synthetic end-to-end demonstration journey."""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from src.application.e2e import run_e2e_journey


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("evidence/e2e"))
    parser.add_argument("--commit", default=None)
    args = parser.parse_args()
    commit = (
        args.commit
        or subprocess.run(
            ["git", "rev-parse", "--short=12", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    )
    with tempfile.TemporaryDirectory(prefix="risco-e2e-") as directory:
        report = run_e2e_journey(args.output, Path(directory), commit)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
