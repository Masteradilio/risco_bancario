"""Partitioned Stage 1 processing with a versioned, bounded result cache."""

from __future__ import annotations

import json
from collections import OrderedDict
from collections.abc import Callable, Iterable, Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from functools import lru_cache
from hashlib import sha256
from itertools import islice
from threading import RLock

import numpy as np

from ...domain.scenarios import ScenarioSet
from ...models.forward_looking import MacroRiskPolicy
from ..calculation import (
    Stage1ContractInput,
    Stage1ECLResult,
    Stage1RiskPeriod,
    calculate_stage1_ecl,
)


@dataclass(frozen=True, slots=True)
class BatchECLRecord:
    contract_id: str
    probability_weighted_ecl: Decimal
    stress_ecl: Decimal
    profile_hash: str


@dataclass(frozen=True, slots=True)
class BatchSummary:
    contract_count: int
    partition_count: int
    maximum_partition_size: int
    unique_profile_calculations: int
    profile_reuses: int
    probability_weighted_ecl: Decimal
    stress_ecl: Decimal
    scenario_version: str
    scenario_hash: str
    macro_policy_version: str
    macro_policy_hash: str


class VersionedResultCache:
    """Thread-safe LRU whose content key includes every external calculation version."""

    def __init__(self, capacity: int = 10_000) -> None:
        if capacity <= 0:
            raise ValueError("cache capacity must be positive")
        self.capacity = capacity
        self._values: OrderedDict[str, Stage1ECLResult] = OrderedDict()
        self._lock = RLock()

    def get(self, key: str) -> Stage1ECLResult | None:
        with self._lock:
            value = self._values.get(key)
            if value is not None:
                self._values.move_to_end(key)
            return value

    def put(self, key: str, value: Stage1ECLResult) -> None:
        with self._lock:
            self._values[key] = value
            self._values.move_to_end(key)
            while len(self._values) > self.capacity:
                self._values.popitem(last=False)


def _partition(
    values: Iterable[Stage1ContractInput], size: int
) -> Iterator[list[Stage1ContractInput]]:
    iterator = iter(values)
    while partition := list(islice(iterator, size)):
        yield partition


def _cents_array(values: Iterable[Decimal]) -> np.ndarray:
    cents = [int(value * 100) for value in values]
    limit = np.iinfo(np.int64).max
    if any(abs(value) > limit for value in cents) or sum(abs(value) for value in cents) > limit:
        raise OverflowError("partition monetary total exceeds safe int64 vector range")
    return np.asarray(cents, dtype=np.int64)


@lru_cache(maxsize=10_000)
def _profile_hash_cached(
    reporting_date: date,
    eir: Decimal,
    segment: str,
    periods: tuple[Stage1RiskPeriod, ...],
    scenario_version: str,
    scenario_hash: str,
    macro_policy_version: str,
    macro_policy_hash: str,
) -> str:
    payload = {
        "reporting_date": str(reporting_date),
        "eir": str(eir),
        "segment": segment,
        "periods": [
            {
                "date": period.reference_date.isoformat(),
                "hazard": str(period.conditional_hazard),
                "lgd": str(period.lifetime_lgd),
                "drawn_ead": str(period.drawn_ead),
                "undrawn": str(period.undrawn_amount),
                "ccf": str(period.ccf),
            }
            for period in periods
        ],
        "scenario_version": scenario_version,
        "scenario_hash": scenario_hash,
        "macro_policy_version": macro_policy_version,
        "macro_policy_hash": macro_policy_hash,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _profile_hash(
    contract: Stage1ContractInput,
    scenario_set: ScenarioSet,
    macro_policy: MacroRiskPolicy,
) -> str:
    return _profile_hash_cached(
        contract.reporting_date,
        contract.original_effective_interest_rate,
        contract.segment,
        contract.periods,
        scenario_set.version,
        scenario_set.source_snapshot_hash,
        macro_policy.policy_version,
        macro_policy.sha256,
    )


class PartitionedStage1Processor:
    """Stream contracts in bounded partitions and retain no per-contract result list."""

    def __init__(
        self,
        scenario_set: ScenarioSet,
        macro_policy: MacroRiskPolicy,
        *,
        partition_size: int = 10_000,
        workers: int = 1,
        cache: VersionedResultCache | None = None,
    ) -> None:
        if partition_size <= 0 or workers <= 0:
            raise ValueError("partition size and workers must be positive")
        self.scenario_set = scenario_set
        self.macro_policy = macro_policy
        self.partition_size = partition_size
        self.workers = workers
        self.cache = cache or VersionedResultCache()

    def _calculate(self, item: tuple[str, Stage1ContractInput]) -> tuple[str, Stage1ECLResult]:
        key, contract = item
        return key, calculate_stage1_ecl(contract, self.scenario_set, self.macro_policy)

    def process(
        self,
        contracts: Iterable[Stage1ContractInput],
        *,
        sink: Callable[[BatchECLRecord], None] | None = None,
    ) -> BatchSummary:
        contract_count = 0
        partition_count = 0
        maximum_partition_size = 0
        unique_calculations = 0
        total_weighted_cents = 0
        total_stress_cents = 0

        with ThreadPoolExecutor(
            max_workers=self.workers, thread_name_prefix="ecl-partition"
        ) as pool:
            for partition in _partition(contracts, self.partition_size):
                partition_count += 1
                maximum_partition_size = max(maximum_partition_size, len(partition))
                keys = [
                    _profile_hash(contract, self.scenario_set, self.macro_policy)
                    for contract in partition
                ]
                resolved: dict[str, Stage1ECLResult] = {}
                missing: dict[str, Stage1ContractInput] = {}
                for key, contract in zip(keys, partition, strict=True):
                    if key in resolved or key in missing:
                        continue
                    cached = self.cache.get(key)
                    if cached is None:
                        missing[key] = contract
                    else:
                        resolved[key] = cached
                for key, result in pool.map(self._calculate, missing.items()):
                    resolved[key] = result
                    self.cache.put(key, result)
                    unique_calculations += 1

                weighted_cents = _cents_array(
                    resolved[key].scenario_ecl.probability_weighted_ecl for key in keys
                )
                stress_cents = _cents_array(resolved[key].scenario_ecl.stress_ecl for key in keys)
                total_weighted_cents += int(weighted_cents.sum(dtype=np.int64))
                total_stress_cents += int(stress_cents.sum(dtype=np.int64))
                contract_count += len(partition)
                if sink:
                    for contract, key, weighted, stress in zip(
                        partition, keys, weighted_cents, stress_cents, strict=True
                    ):
                        sink(
                            BatchECLRecord(
                                contract.contract_id,
                                Decimal(int(weighted)) / 100,
                                Decimal(int(stress)) / 100,
                                key,
                            )
                        )

        return BatchSummary(
            contract_count=contract_count,
            partition_count=partition_count,
            maximum_partition_size=maximum_partition_size,
            unique_profile_calculations=unique_calculations,
            profile_reuses=max(0, contract_count - unique_calculations),
            probability_weighted_ecl=Decimal(total_weighted_cents) / 100,
            stress_ecl=Decimal(total_stress_cents) / 100,
            scenario_version=self.scenario_set.version,
            scenario_hash=self.scenario_set.source_snapshot_hash,
            macro_policy_version=self.macro_policy.policy_version,
            macro_policy_hash=self.macro_policy.sha256,
        )
