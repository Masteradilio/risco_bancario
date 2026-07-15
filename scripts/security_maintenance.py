"""Purge eligible ephemeral records and generated exports under the retention policy."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path

from src.audit import AuditService
from src.infrastructure.database import DatabaseManager
from src.infrastructure.database.startup import prepare_database
from src.security.files import SecureExportStore
from src.security.retention import load_retention_policy, purge_ephemeral_records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, default=Path("config/security/retention.json"))
    parser.add_argument("--exports-root", type=Path, default=Path("var/private-exports"))
    arguments = parser.parse_args()

    database = DatabaseManager()
    prepare_database(database, mode="validate")
    policy = load_retention_policy(arguments.policy)
    current = datetime.now(UTC)
    result = purge_ephemeral_records(database, policy, now=current)
    deleted_exports = SecureExportStore(arguments.exports_root).purge_older_than(
        current - timedelta(days=policy.generated_exports_days)
    )
    summary = {**asdict(result), "deleted_exports": deleted_exports}
    AuditService(database).record(
        actor_id="system:retention",
        actor_role=None,
        action="RETENTION_PURGE",
        resource_type="ephemeral_records",
        resource_id=policy.policy_version,
        input_payload={"policy_version": policy.policy_version},
        result_payload=summary,
        versions={"retention_policy": policy.policy_version},
        status="SUCCEEDED",
    )
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
