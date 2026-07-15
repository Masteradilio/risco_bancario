"""Reproducible bounded-memory benchmark for 10k, 100k and 1m Stage 1 contracts."""

from __future__ import annotations

import argparse
import json
import platform
import sys
import time
import tracemalloc
from collections.abc import Iterator
from dataclasses import asdict
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

from src.application.services import load_scenario_set
from src.ecl.batch import PartitionedStage1Processor
from src.ecl.calculation import Stage1ContractInput, Stage1RiskPeriod
from src.models.forward_looking import load_macro_risk_policy

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGETS = ROOT / "config/performance/targets.json"
DEFAULT_OUTPUT = ROOT / "evidence/performance/batch-benchmark.json"


def synthetic_contracts(count: int, *, profiles: int = 64) -> Iterator[Stage1ContractInput]:
    """Yield unique contract IDs over a deterministic cohort of risk profiles."""
    templates = tuple(
        tuple(
            Stage1RiskPeriod(
                date(2026, month, 1),
                Decimal("0.005") + Decimal(profile % 8) / 1000,
                Decimal("0.30") + Decimal(profile % 5) / 100,
                Decimal(900 + profile * 10 - (month - 1) * 40),
                Decimal(100 + profile),
                Decimal("0.40") + Decimal(profile % 4) / 100,
            )
            for month in range(1, 13)
        )
        for profile in range(profiles)
    )
    for index in range(count):
        yield Stage1ContractInput(
            f"CTR-BENCH-{index:09d}",
            date(2025, 12, 31),
            Decimal("0.12"),
            templates[index % profiles],
            "portfolio",
        )


def run_case(size: int, partition_size: int, workers: int) -> dict[str, object]:
    scenario_set = load_scenario_set(seed=91)
    macro_policy = load_macro_risk_policy()
    processor = PartitionedStage1Processor(
        scenario_set,
        macro_policy,
        partition_size=partition_size,
        workers=workers,
    )
    tracemalloc.start()
    started = time.perf_counter()
    summary = processor.process(synthetic_contracts(size))
    elapsed = time.perf_counter() - started
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        **asdict(summary),
        "probability_weighted_ecl": str(summary.probability_weighted_ecl),
        "stress_ecl": str(summary.stress_ecl),
        "elapsed_seconds": round(elapsed, 6),
        "throughput_contracts_per_second": round(size / elapsed, 2),
        "python_peak_memory_bytes": peak_bytes,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", type=int, nargs="+", default=[10_000, 100_000, 1_000_000])
    parser.add_argument("--partition-size", type=int, default=10_000)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--targets", type=Path, default=DEFAULT_TARGETS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    if any(size <= 0 for size in arguments.sizes):
        parser.error("sizes must be positive")
    targets = json.loads(arguments.targets.read_text(encoding="utf-8"))
    results = [
        run_case(size, arguments.partition_size, arguments.workers) for size in arguments.sizes
    ]
    million = next((item for item in results if item["contract_count"] == 1_000_000), None)
    target_result = "not_evaluated"
    if million:
        target_result = (
            "passed"
            if million["elapsed_seconds"] <= targets["one_million"]["max_elapsed_seconds"]
            and million["python_peak_memory_bytes"]
            <= targets["one_million"]["max_python_peak_memory_bytes"]
            else "failed"
        )
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "runtime": {"python": sys.version, "platform": platform.platform()},
        "methodology": {
            "data_classification": "synthetic",
            "risk_profiles": 64,
            "unique_contract_ids": True,
            "partition_size": arguments.partition_size,
            "workers": arguments.workers,
            "result_retention": "aggregate_only",
            "memory_measurement": "tracemalloc_python_allocations",
        },
        "targets": targets,
        "target_result": target_result,
        "results": results,
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    if target_result == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
