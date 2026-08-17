from datetime import date
from pathlib import Path

import pytest

from src.agent.evidence import ExecutionNotFoundError, GroundedEvidenceAgent
from src.agent.models import AgentQuery
from src.infrastructure.database import DatabaseManager, DatabaseSettings, VersionedRepository


def test_agent_rejects_missing_execution_and_execution_without_results(tmp_path: Path) -> None:
    database = DatabaseManager(
        DatabaseSettings(backend="sqlite", sqlite_path=tmp_path / "agent.sqlite3")
    )
    database.apply_migrations()
    agent = GroundedEvidenceAgent(database)
    with pytest.raises(ExecutionNotFoundError, match="missing"):
        agent.answer(AgentQuery(execution_id="missing", question="resuma"))

    execution = VersionedRepository(database).start_execution(
        execution_key="empty",
        reference_date=date(2026, 7, 1),
        lineage={"code": "abcdef1"},
    )
    with pytest.raises(ExecutionNotFoundError, match="without results"):
        agent.answer(AgentQuery(execution_id=execution["execution_id"], question="resuma"))
