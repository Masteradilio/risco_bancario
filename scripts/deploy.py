"""Plan promotions, run controlled migrations, and record application rollback state."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from src.infrastructure.database import DatabaseManager
from src.infrastructure.database.startup import prepare_database
from src.infrastructure.deployment import DeploymentStateStore, load_environment_profile

ROOT = Path(__file__).resolve().parents[1]


def _emit(payload: object, output: Path | None) -> None:
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("plan", "promote", "rollback", "migrate"))
    parser.add_argument("--environment", required=True, choices=("local", "test", "demo"))
    parser.add_argument("--image-tag")
    parser.add_argument("--commit", default=os.getenv("GITHUB_SHA", "unknown"))
    parser.add_argument("--state-file", type=Path, default=ROOT / "var/deployments/state.json")
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    profile = load_environment_profile(arguments.environment)

    if arguments.action == "migrate":
        if arguments.env_file:
            from dotenv import load_dotenv

            load_dotenv(arguments.env_file, override=True)
        if os.getenv("APP_ENV", arguments.environment) != arguments.environment:
            parser.error("APP_ENV does not match --environment")
        database = DatabaseManager()
        if database.settings.backend != profile.database_backend:
            parser.error("configured database backend does not match the environment profile")
        applied = prepare_database(database, mode="apply")
        _emit({"environment": profile.name, "applied": applied}, arguments.output)
        return

    store = DeploymentStateStore(arguments.state_file)
    if arguments.action == "rollback":
        _emit(store.rollback(profile), arguments.output)
        return
    if not arguments.image_tag:
        parser.error("--image-tag is required for plan and promote")
    operation = store.plan if arguments.action == "plan" else store.promote
    _emit(operation(profile, arguments.image_tag, arguments.commit), arguments.output)


if __name__ == "__main__":
    main()
