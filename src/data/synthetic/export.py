"""Deterministic Parquet materialization for the synthetic data factory."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pyarrow as pa  # type: ignore[import-untyped]
import pyarrow.parquet as pq  # type: ignore[import-untyped]

from .events import CreditEventHistory, generate_credit_events
from .longitudinal import LongitudinalPortfolio, generate_monthly_history
from .macroeconomics import MacroeconomicBundle, generate_macroeconomic_bundle
from .modeling import ModelingDatasets, build_modeling_datasets
from .population import PopulationConfig, SyntheticPortfolio, generate_population
from .quality import assess_synthetic_quality

FACTORY_VERSION = "0.1.0"
REQUIRED_DATASETS = (
    "clients",
    "contracts",
    "monthly_snapshots",
    "payments",
    "delinquencies",
    "defaults",
    "recoveries",
    "collateral",
    "limits_and_drawdowns",
    "macro_scenarios",
    "writeoffs",
    "regulatory_reporting_input",
    "pd_modeling",
    "lgd_modeling",
    "ead_modeling",
    "sicr_modeling",
)


def _rows(items: tuple[Any, ...]) -> list[dict[str, object]]:
    return [asdict(item) for item in items]


def _derived_snapshot_tables(
    history: LongitudinalPortfolio,
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    payments: list[dict[str, object]] = []
    delinquencies: list[dict[str, object]] = []
    limits: list[dict[str, object]] = []
    previous_balance: dict[str, Decimal] = {}
    for item in history.snapshots:
        payments.append(
            {
                "contract_id": item.contract_id,
                "client_id": item.client_id,
                "reference_date": item.reference_date,
                "scheduled_payment": item.scheduled_payment,
                "paid_amount": item.paid_amount,
            }
        )
        delinquencies.append(
            {
                "contract_id": item.contract_id,
                "reference_date": item.reference_date,
                "days_past_due": item.days_past_due,
            }
        )
        prior = previous_balance.get(item.contract_id, item.balance)
        drawdown = max(type(item.balance)("0"), item.balance - prior)
        limits.append(
            {
                "contract_id": item.contract_id,
                "reference_date": item.reference_date,
                "credit_limit": item.credit_limit,
                "drawn_balance": item.balance,
                "monthly_drawdown": drawdown,
                "utilization": item.utilization,
            }
        )
        previous_balance[item.contract_id] = item.balance
    return payments, delinquencies, limits


def _regulatory_source_rows(
    population: SyntheticPortfolio, history: LongitudinalPortfolio
) -> list[dict[str, object]]:
    contracts = {item.contract_id: item for item in population.contracts}
    latest = {}
    for snapshot in history.snapshots:
        latest[snapshot.contract_id] = snapshot
    rows: list[dict[str, object]] = []
    for contract_id in sorted(latest):
        snapshot = latest[contract_id]
        contract = contracts[contract_id]
        rows.append(
            {
                "reference_date": snapshot.reference_date,
                "contract_id": contract.contract_id,
                "client_id": contract.client_id,
                "counterparty_id": contract.counterparty_id,
                "product_code": contract.product_code,
                "facility_type": contract.facility_type,
                "origination_date": contract.origination_date,
                "maturity_date": contract.maturity_date,
                "currency": contract.currency,
                "balance": snapshot.balance,
                "credit_limit": snapshot.credit_limit,
                "days_past_due": snapshot.days_past_due,
                "acquired_credit_impaired": contract.acquired_credit_impaired,
                "policy_version": snapshot.policy_version,
            }
        )
    return rows


def _tables(
    population: SyntheticPortfolio,
    history: LongitudinalPortfolio,
    events: CreditEventHistory,
    macro: MacroeconomicBundle,
    modeling: ModelingDatasets,
) -> dict[str, list[dict[str, object]]]:
    payments, delinquencies, limits = _derived_snapshot_tables(history)
    return {
        "economic_groups": _rows(population.groups),
        "counterparties": _rows(population.counterparties),
        "clients": _rows(population.clients),
        "contracts": _rows(population.contracts),
        "schedules": _rows(population.schedules),
        "collateral": _rows(population.collateral),
        "monthly_snapshots": _rows(history.snapshots),
        "modifications": _rows(history.modifications),
        "payments": payments,
        "delinquencies": delinquencies,
        "limits_and_drawdowns": limits,
        "defaults": _rows(events.defaults),
        "collections": _rows(events.collections),
        "recoveries": _rows(events.recoveries),
        "cures": _rows(events.cures),
        "writeoffs": _rows(events.writeoffs),
        "macro_observed": _rows(macro.observed),
        "macro_scenarios": _rows(macro.scenarios),
        "scenario_weights": [
            {"scenario_id": scenario_id, "weight": weight}
            for scenario_id, weight in macro.scenario_weights
        ],
        "regulatory_reporting_input": _regulatory_source_rows(population, history),
        "pd_modeling": _rows(modeling.pd),
        "lgd_modeling": _rows(modeling.lgd),
        "ead_modeling": _rows(modeling.ead),
        "sicr_modeling": _rows(modeling.sicr),
    }


def _write_table(path: Path, rows: list[dict[str, object]]) -> pa.Schema:
    if not rows:
        raise ValueError(f"cannot materialize empty dataset: {path.stem}")
    table = pa.Table.from_pylist(rows)
    pq.write_table(
        table,
        path,
        compression="zstd",
        version="2.6",
        use_dictionary=False,
        write_statistics=True,
    )
    return table.schema


def _file_hash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def materialize_synthetic_factory(
    output_dir: Path,
    *,
    seed: int = 91,
    clients: int = 40,
    contracts_per_client: int = 2,
) -> Path:
    population = generate_population(
        PopulationConfig(seed=seed, clients=clients, contracts_per_client=contracts_per_client)
    )
    history = generate_monthly_history(population)
    events = generate_credit_events(population, history)
    macro = generate_macroeconomic_bundle(seed)
    modeling = build_modeling_datasets(population, history, events, macro)
    quality = assess_synthetic_quality(population, history, events, macro, modeling)
    if not quality.passed:
        raise ValueError(f"synthetic quality gate failed: {quality.issues}")

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_files: dict[str, dict[str, object]] = {}
    for name, rows in sorted(_tables(population, history, events, macro, modeling).items()):
        path = output_dir / f"{name}.parquet"
        schema = _write_table(path, rows)
        manifest_files[path.name] = {
            "rows": len(rows),
            "sha256": _file_hash(path),
            "schema": [{"name": field.name, "type": str(field.type)} for field in schema],
        }

    missing = [name for name in REQUIRED_DATASETS if f"{name}.parquet" not in manifest_files]
    if missing:
        raise ValueError(f"missing required datasets: {missing}")
    manifest = {
        "manifest_version": "1.0.0",
        "factory_version": FACTORY_VERSION,
        "seed": seed,
        "parameters": {
            "clients": clients,
            "contracts_per_client": contracts_per_client,
        },
        "component_versions": {
            "population": population.generator_version,
            "longitudinal": history.generator_version,
            "events": events.generator_version,
            "macroeconomics": macro.policy_version,
            "modeling": modeling.version,
        },
        "macroeconomic_policy_sha256": macro.policy_hash,
        "files": manifest_files,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=91)
    parser.add_argument("--clients", type=int, default=40)
    parser.add_argument("--contracts-per-client", type=int, default=2)
    args = parser.parse_args()
    manifest = materialize_synthetic_factory(
        args.output,
        seed=args.seed,
        clients=args.clients,
        contracts_per_client=args.contracts_per_client,
    )
    print(manifest)


if __name__ == "__main__":
    main()
