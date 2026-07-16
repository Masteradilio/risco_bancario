from __future__ import annotations

import json
from concurrent.futures import Future
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from threading import Event

import pytest

from scripts.performance_benchmark import synthetic_contracts
from src.application.services import load_scenario_set
from src.ecl.batch import BatchQueueFullError, BoundedBatchExecutor, PartitionedStage1Processor
from src.ecl.batch.processor import VersionedResultCache, _cents_array
from src.ecl.calculation import calculate_stage1_ecl
from src.infrastructure.database import DatabaseManager, DatabaseSettings
from src.interfaces.api.jobs import JobStore
from src.models.forward_looking import load_macro_risk_policy


def test_partitioned_processor_matches_canonical_and_streams_results() -> None:
    contracts = list(synthetic_contracts(130, profiles=3))
    scenario_set = load_scenario_set(seed=91)
    policy = load_macro_risk_policy()
    records = []
    summary = PartitionedStage1Processor(
        scenario_set, policy, partition_size=32, workers=2
    ).process(contracts, sink=records.append)
    first = calculate_stage1_ecl(contracts[0], scenario_set, policy)

    assert summary.contract_count == 130
    assert summary.partition_count == 5 and summary.maximum_partition_size == 32
    assert summary.unique_profile_calculations == 3 and summary.profile_reuses == 127
    assert records[0].probability_weighted_ecl == first.scenario_ecl.probability_weighted_ecl
    assert len(records) == 130


def test_cache_key_changes_with_scenario_and_policy_versions() -> None:
    contract = next(synthetic_contracts(1))
    scenario_set = load_scenario_set(seed=91)
    policy = load_macro_risk_policy()
    cache = VersionedResultCache()
    first = PartitionedStage1Processor(scenario_set, policy, cache=cache).process([contract])
    changed_scenario = replace(scenario_set, source_snapshot_hash="f" * 64)
    second = PartitionedStage1Processor(changed_scenario, policy, cache=cache).process([contract])
    changed_policy = replace(policy, sha256="e" * 64)
    third = PartitionedStage1Processor(scenario_set, changed_policy, cache=cache).process(
        [contract]
    )

    assert first.unique_profile_calculations == 1
    assert second.unique_profile_calculations == 1
    assert third.unique_profile_calculations == 1


def test_batch_cache_and_processor_reject_invalid_capacity_and_evict_lru() -> None:
    with pytest.raises(ValueError, match="cache capacity"):
        VersionedResultCache(capacity=0)
    with pytest.raises(ValueError, match="partition size"):
        PartitionedStage1Processor(
            load_scenario_set(seed=91), load_macro_risk_policy(), partition_size=0
        )

    contracts = list(synthetic_contracts(2, profiles=2))
    cache = VersionedResultCache(capacity=1)
    processor = PartitionedStage1Processor(
        load_scenario_set(seed=91), load_macro_risk_policy(), cache=cache
    )
    summary = processor.process(contracts)
    assert summary.unique_profile_calculations == 2
    assert len(cache._values) == 1


def test_ten_thousand_contracts_remain_partition_bounded() -> None:
    summary = PartitionedStage1Processor(
        load_scenario_set(seed=91),
        load_macro_risk_policy(),
        partition_size=1_000,
        workers=4,
    ).process(synthetic_contracts(10_000))

    assert summary.contract_count == 10_000
    assert summary.partition_count == 10
    assert summary.maximum_partition_size == 1_000
    assert summary.unique_profile_calculations == 64
    assert summary.probability_weighted_ecl > Decimal("0")


def test_bounded_queue_applies_backpressure_and_completes_concurrently() -> None:
    queue = BoundedBatchExecutor(workers=1, queue_capacity=1)
    started = Event()
    release = Event()

    def blocked(value: int) -> int:
        started.set()
        assert release.wait(timeout=2)
        return value

    first: Future[int] = queue.submit(blocked, 1)
    assert started.wait(timeout=1)
    second: Future[int] = queue.submit(blocked, 2)
    with pytest.raises(BatchQueueFullError, match="capacity"):
        queue.submit(blocked, 3)
    release.set()

    assert first.result(timeout=2) == 1
    assert second.result(timeout=2) == 2
    queue.shutdown()


def test_performance_target_is_explicit_and_not_an_institutional_sla() -> None:
    target = Path("config/performance/targets.json").read_text(encoding="utf-8")
    assert "demonstrative_capacity_target" in target
    assert "120" in target and "536870912" in target


def test_vectorized_monetary_aggregation_rejects_int64_overflow() -> None:
    with pytest.raises(OverflowError, match="int64"):
        _cents_array([Decimal("92233720368547758.08")])


def test_interrupted_persisted_jobs_are_failed_for_explicit_resubmission(tmp_path: Path) -> None:
    database = DatabaseManager(DatabaseSettings(sqlite_path=tmp_path / "queue.sqlite3"))
    database.apply_migrations()
    jobs = JobStore(database)
    pending = jobs.create("{}")
    running = jobs.create('{"batch":2}')
    jobs.running(running)

    assert jobs.fail_interrupted() == 2
    assert jobs.get(pending)["error_code"] == "PROCESS_RESTARTED"
    assert jobs.get(running)["status"] == "FAILED"


def test_committed_benchmark_proves_all_required_volumes_and_versions() -> None:
    evidence = json.loads(
        Path("evidence/performance/batch-benchmark.json").read_text(encoding="utf-8")
    )
    results = {item["contract_count"]: item for item in evidence["results"]}

    assert set(results) == {10_000, 100_000, 1_000_000}
    assert evidence["target_result"] == "passed"
    assert results[1_000_000]["maximum_partition_size"] == 10_000
    assert results[1_000_000]["scenario_hash"] == results[10_000]["scenario_hash"]
    assert results[1_000_000]["macro_policy_hash"] == results[10_000]["macro_policy_hash"]
