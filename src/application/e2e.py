"""Canonical, fail-closed synthetic journey for release evidence."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, date, datetime
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

from ..data.synthetic import (
    PopulationConfig,
    build_modeling_datasets,
    generate_credit_events,
    generate_macroeconomic_bundle,
    generate_monthly_history,
    generate_population,
)
from ..data.synthetic.export import materialize_synthetic_factory
from ..ecl.overlays.management import ManagementOverlay, apply_management_overlays
from ..infrastructure.database import DatabaseManager, DatabaseSettings, VersionedRepository
from ..interfaces.api.schemas import ECLCalculationRequest
from ..interfaces.api.service import CanonicalECLApiService
from ..models.ead import (
    build_amortized_default_ead_dataset,
    build_revolving_ccf_dataset,
    fit_revolving_ccf_model,
    load_amortized_ead_policy,
    load_ead_validation_policy,
    load_off_balance_ead_policy,
    load_revolving_ccf_policy,
    validate_ead_models,
)
from ..models.lgd import (
    build_lgd_modeling_dataset,
    build_lgd_workout_dataset,
    calculate_realized_lgd_dataset,
    fit_lgd_models,
    load_lgd_validation_policy,
    load_realized_lgd_policy,
    validate_lgd_model,
)
from ..models.pd import fit_explainable_baselines, validate_frozen_pd
from ..models.sicr.validation import validate_sicr_staging
from ..regulatory.cmn4966.provision_floor import ProvisionPortfolio, apply_provision_floor
from ..regulatory.doc3040 import (
    Accounting4966,
    Client,
    Doc3040Input,
    Header,
    MaturityValue,
    Operation,
    PortfolioEclControl,
    generate_xml_candidate,
    prevalidate_xml,
    sourced,
)
from ..validation.reconciliation.ecl_ledger import (
    ContractECLAdjustment,
    ECLLedgerEntry,
    create_ecl_execution_ledger,
)

REFERENCE_DATE = date(2026, 6, 30)
PERIOD_DATE = date(2026, 7, 1)
POLICY_VERSION = "2026.07.1"
CONFIG_HASH = sha256(b"canonical-e2e-2026.07.1").hexdigest()


def _jsonable(value: Any) -> Any:
    if isinstance(value, (date, datetime, Decimal, Path)):
        return str(value)
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    return value


def _payload(commit: str) -> ECLCalculationRequest:
    variables = {
        "gdp_growth": "2.20",
        "inflation": "4.50",
        "policy_rate": "9.00",
        "unemployment": "7.50",
        "household_debt": "49.00",
        "risk_pressure": "0.00",
    }
    scenarios: list[dict[str, Any]] = [
        {"scenario_id": "base", "name": "Base", "kind": "base", "weight": "0.50"},
        {"scenario_id": "upside", "name": "Up", "kind": "upside", "weight": "0.20"},
        {"scenario_id": "downside", "name": "Down", "kind": "downside", "weight": "0.30"},
        {"scenario_id": "stress", "name": "Stress", "kind": "stress", "weight": "0"},
    ]
    for scenario in scenarios:
        scenario["periods"] = [{"reference_date": str(PERIOD_DATE), "variables": variables}]
    return ECLCalculationRequest.model_validate(
        {
            "execution_key": "e2e:synthetic:2026-06-30",
            "contract_id": "CONTRATO1",
            "source_version": "synthetic-2026.07.1",
            "reference_date": str(REFERENCE_DATE),
            "stage": 1,
            "stage_assessment": {
                "origination_stage": 1,
                "current_stage": 1,
                "origination_rating": "A1",
                "current_rating": "A2",
                "origination_lifetime_pd": "0.05",
                "current_lifetime_pd": "0.10",
                "reason_codes": ["NO_SICR_TRIGGER"],
            },
            "segment": "portfolio",
            "periods": [
                {
                    "reference_date": str(PERIOD_DATE),
                    "conditional_hazard": "0.10",
                    "lgd": "0.40",
                    "drawn_ead": "100.00",
                    "undrawn_amount": "0",
                    "ccf": "0",
                    "discount_factor": "1",
                }
            ],
            "scenario_version": POLICY_VERSION,
            "scenario_source_hash": "a" * 64,
            "scenarios": scenarios,
            "model_versions": {"pd": POLICY_VERSION, "lgd": POLICY_VERSION, "ead": POLICY_VERSION},
            "configuration_version": POLICY_VERSION,
            "configuration_hash": CONFIG_HASH,
            "code_commit": commit,
        }
    )


def _model_evidence() -> tuple[dict[str, Any], dict[str, Any]]:
    population = generate_population(PopulationConfig(seed=91, clients=40, contracts_per_client=2))
    history = generate_monthly_history(population)
    events = generate_credit_events(population, history)
    macro = generate_macroeconomic_bundle(91)
    modeling = build_modeling_datasets(population, history, events, macro)
    baselines = fit_explainable_baselines(modeling)
    pd_report = validate_frozen_pd(modeling)
    sicr_report = validate_sicr_staging(modeling)

    workout = build_lgd_workout_dataset(population, events, observation_end_date=date(2025, 12, 1))
    realized = calculate_realized_lgd_dataset(
        workout, load_realized_lgd_policy(Path("config/lgd_policy/2026.07.1.json"))
    )
    lgd_dataset = build_lgd_modeling_dataset(workout, realized, population, history, macro)
    lgd_comparison = fit_lgd_models(lgd_dataset)
    lgd_report = validate_lgd_model(
        lgd_dataset,
        lgd_comparison,
        load_lgd_validation_policy(Path("config/lgd_validation/2026.07.1.json")),
    )

    ccf_policy = load_revolving_ccf_policy(Path("config/ccf_policy/2026.07.1.json"))
    development = generate_population(
        PopulationConfig(
            seed=ccf_policy.development_seed,
            clients=ccf_policy.development_clients,
            contracts_per_client=ccf_policy.development_contracts_per_client,
        )
    )
    development_history = generate_monthly_history(development)
    development_events = generate_credit_events(development, development_history)
    ccf_dataset = build_revolving_ccf_dataset(
        development, development_history, development_events, ccf_policy
    )
    ccf_model = fit_revolving_ccf_model(ccf_dataset)
    amortized = build_amortized_default_ead_dataset(
        population,
        history,
        events,
        load_amortized_ead_policy(Path("config/ead_policy/2026.07.1.json")),
    )
    ead_report = validate_ead_models(
        amortized,
        ccf_dataset,
        ccf_model,
        load_off_balance_ead_policy(Path("config/off_balance_ead_policy/2026.07.1.json")),
        load_ead_validation_policy(Path("config/ead_validation/2026.07.1.json")),
    )
    evidence = {
        "training": {
            "pd_candidates": [baselines.logistic_12m.name, baselines.discrete_hazard_1m.name],
            "lgd_selected": lgd_report.model_name,
            "ccf_model": ccf_model.name,
        },
        "validation": {
            "pd": {"status": pd_report.approval_status, "sample": pd_report.sample_count},
            "sicr": {"status": sicr_report.approval_status, "sample": sicr_report.sample_count},
            "lgd": {"status": lgd_report.approval_status, "blockers": list(lgd_report.blockers)},
            "ead": {"status": ead_report.approval_status, "blockers": list(ead_report.blockers)},
        },
        "stage_classification": {
            "method": "relative_sicr_validation_proxy",
            "evaluation_split": sicr_report.evaluation_split,
            "sample_count": sicr_report.sample_count,
            "false_positive_count": len(sicr_report.false_positive_contracts),
            "false_negative_count": len(sicr_report.false_negative_contracts),
        },
    }
    return evidence, {"population": population, "history": history, "events": events}


def _sv(value: Any, field: str) -> Any:
    return sourced(value, system="canonical_e2e", field=field, evidence_id=f"E2E-{field}")


def _doc3040(final_ecl: Decimal) -> Doc3040Input:
    accounting = Accounting4966(
        asset_classification=_sv("1", "asset_classification"),
        stage=_sv("1", "stage"),
        instrument_quantity=None,
        gross_carrying_amount=_sv(Decimal("100"), "gross"),
        accumulated_loss=_sv(final_ecl, "loss"),
        fair_value=None,
        effective_interest_rate=_sv(Decimal("12.5"), "eir"),
        monthly_income=None,
        stage_one_pd_type=_sv("N", "pd_type"),
        minimum_provision_portfolio=_sv("C1", "floor"),
        isolated_credit_risk_treatment=_sv("N", "risk"),
        stage_allocations=(),
        recognized_losses=(),
    )
    operation = Operation(
        detailed_client=None,
        ipoc=_sv("123456780203112345678901CONTRATO1", "ipoc"),
        contract_code=_sv("CONTRATO1", "contract"),
        modality=_sv("0203", "modality"),
        cosif_accounts=None,
        resource_origin=_sv("0101", "origin"),
        indexer=_sv("01", "indexer"),
        indexer_percentage=_sv(Decimal("100"), "index_pct"),
        currency_variation=_sv("790", "currency"),
        postal_code=_sv("01310100", "postal"),
        effective_annual_rate=_sv(Decimal("12.5"), "rate"),
        contract_date=_sv(date(2025, 1, 15), "contract_date"),
        contracted_amount=_sv(Decimal("100"), "amount"),
        nature=_sv("01", "nature"),
        maturity_date=_sv(date(2027, 1, 15), "maturity"),
        provision=_sv(final_ecl, "provision"),
        days_past_due=None,
        special_characteristics=None,
        next_installment_date=None,
        next_installment_amount=None,
        installment_count=_sv(1, "installments"),
        maturities=(
            MaturityValue(
                vertex=_sv("v110", "vertex"), amount=_sv(Decimal("100"), "maturity_amount")
            ),
        ),
        guarantees=(),
        additional_information=(),
        sicor=None,
        accounting_4966=accounting,
    )
    client = Client(
        code=_sv("12345678901", "client_code"),
        client_type=_sv("1", "client_type"),
        authorization=_sv("S", "authorization"),
        client_size=_sv("1", "client_size"),
        control_type=None,
        relationship_start=_sv(date(2020, 1, 15), "relationship"),
        income=_sv(Decimal("5000"), "income"),
        economic_group=None,
        foreign_name=None,
        foreign_id_type=None,
        foreign_id=None,
        leader_cnpj=None,
        country_code=None,
        operations=(operation,),
    )
    header = Header(
        reference_month=_sv(date(2026, 7, 1), "reference_month"),
        reporting_entity_cnpj=_sv("12345678", "entity"),
        part=_sv(1, "part"),
        remittance=_sv(1, "remittance"),
        file_type=_sv("F", "file_type"),
        responsible_name=_sv("Responsavel E2E", "responsible"),
        responsible_email=_sv("e2e@example.test", "email"),
        responsible_phone=_sv("1133334444", "phone"),
        total_clients=_sv(1, "total_clients"),
        expected_loss_methodology=_sv("C", "methodology"),
        differentiated_eir_method=_sv("N", "eir_method"),
        fund_type=None,
    )
    return Doc3040Input(header=header, clients=(client,), aggregations=(), connected_ipoc_groups=())


def run_e2e_journey(output_dir: Path, work_dir: Path, code_commit: str) -> dict[str, Any]:
    """Run the full demonstrative journey and write independently inspectable evidence."""
    manifest_path = materialize_synthetic_factory(work_dir / "synthetic")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    model_evidence, _ = _model_evidence()
    database = DatabaseManager(
        DatabaseSettings(backend="sqlite", sqlite_path=work_dir / "e2e.sqlite3")
    )
    migrations = database.apply_migrations()
    response = CanonicalECLApiService(VersionedRepository(database)).calculate(
        _payload(code_commit)
    )

    overlay = apply_management_overlays(
        response.probability_weighted_ecl,
        (
            ManagementOverlay(
                overlay_id="E2E-OVERLAY-1",
                amount="1.00",
                reason="synthetic demonstration",
                approved_by="independent-demo-review",
                approved_at=datetime(2026, 6, 30, tzinfo=UTC),
                effective_from=REFERENCE_DATE,
                effective_to=date(2026, 12, 31),
                version=POLICY_VERSION,
            ),
        ),
        REFERENCE_DATE,
    )
    floor = apply_provision_floor(
        reference_date=REFERENCE_DATE,
        portfolio=ProvisionPortfolio.C1,
        gross_carrying_amount="100",
        calculated_ecl=overlay.final_ecl,
        days_past_due=0,
        default_date=None,
    )
    final_ecl = floor.final_provision
    entries = tuple(
        ECLLedgerEntry(
            "CONTRATO1",
            "CLIENTE1",
            "personal_loan",
            PERIOD_DATE,
            scenario.scenario_id,
            scenario.weight,
            scenario.periods[0].expected_loss,
        )
        for scenario in response.scenarios
        if scenario.weight > 0
    )
    ledger = create_ecl_execution_ledger(
        execution_id=response.execution_id,
        reference_date=REFERENCE_DATE,
        created_at=datetime(2026, 7, 1, tzinfo=UTC),
        entries=entries,
        adjustments=(
            ContractECLAdjustment(
                "CONTRATO1",
                response.probability_weighted_ecl,
                overlay.overlay_amount,
                floor.regulatory_floor,
                final_ecl,
            ),
        ),
        model_version=POLICY_VERSION,
        configuration_version=POLICY_VERSION,
        configuration_hash=CONFIG_HASH,
    )
    candidate = generate_xml_candidate(_doc3040(final_ecl))
    prevalidation = prevalidate_xml(
        candidate.content,
        (
            PortfolioEclControl(
                "123456780203112345678901CONTRATO1", Decimal("100"), final_ecl, ledger.ledger_hash
            ),
        ),
    )
    blockers = [
        component
        for component, evidence in model_evidence["validation"].items()
        if evidence["status"] != "approved"
    ]
    status = "COMPLETED_WITH_MODEL_APPROVAL_BLOCKERS" if blockers else "COMPLETED"
    execution_row = database.fetch_one(
        "SELECT status FROM calculation_executions WHERE execution_id = ?",
        (response.execution_id,),
    )
    result_count = database.fetch_one(
        "SELECT COUNT(*) AS count FROM calculation_results WHERE execution_id = ?",
        (response.execution_id,),
    )
    if execution_row is None or result_count is None:
        raise RuntimeError("persisted ECL execution could not be reconciled")
    report = {
        "schema_version": "1.0.0",
        "mode": "synthetic_demonstration",
        "status": status,
        "code_commit": code_commit,
        "reference_date": str(REFERENCE_DATE),
        "synthetic_factory": {
            "manifest_sha256": sha256(manifest_path.read_bytes()).hexdigest(),
            "files": len(manifest["files"]),
            "rows": sum(item["rows"] for item in manifest["files"].values()),
        },
        "models": model_evidence,
        "approval_blockers": blockers,
        "ecl": {
            "execution_id": response.execution_id,
            "stage": response.stage,
            "economic_ecl": str(response.probability_weighted_ecl),
            "stress_ecl": str(response.stress_ecl),
            "management_overlay": str(overlay.overlay_amount),
            "regulatory_floor": str(floor.regulatory_floor),
            "final_ecl": str(final_ecl),
            "ledger_hash": ledger.ledger_hash,
            "reconciled": ledger.reconciliation.reconciled,
        },
        "persistence": {
            "backend": "sqlite",
            "migrations_applied": list(migrations),
            "execution_status": execution_row["status"],
            "result_rows": result_count["count"],
        },
        "doc3040": {
            "candidate_sha256": candidate.sha256,
            "layout_version": candidate.layout_version,
            "prevalidation_status": prevalidation.status,
            "passed": prevalidation.passed,
            "official_xsd_executed": prevalidation.official_xsd_executed,
            "official_critics_executed": prevalidation.official_critics_executed,
            "warnings": [item.rule_id for item in prevalidation.issues],
        },
        "frontend_and_audit": {
            "frontend_contract": "/api/v1/ecl/executions/{execution_id}",
            "lineage_hash": response.lineage_hash,
            "auditability": "persisted_execution_and_immutable_ledger_hash",
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "doc3040.xml").write_bytes(candidate.content)
    (output_dir / "prevalidation.json").write_text(
        json.dumps(_jsonable(asdict(prevalidation)), ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (output_dir / "journey.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (output_dir / "report.md").write_text(
        "# Jornada E2E canônica\n\n"
        f"- Status: `{status}`\n"
        f"- Execução ECL: `{response.execution_id}`\n"
        f"- ECL econômico / overlay / piso / final: {response.probability_weighted_ecl} / "
        f"{overlay.overlay_amount} / {floor.regulatory_floor} / {final_ecl}\n"
        f"- Reconciliação: `{ledger.reconciliation.reconciled}`; ledger `{ledger.ledger_hash}`\n"
        f"- Doc3040: `{prevalidation.status}`; XSD oficial executado: "
        f"`{prevalidation.official_xsd_executed}`; críticas oficiais executadas: "
        f"`{prevalidation.official_critics_executed}`\n"
        f"- Bloqueios de aprovação: {', '.join(blockers)}\n\n"
        "Esta evidência usa somente dados sintéticos e não representa homologação institucional "
        "ou validação oficial do Documento 3040.\n",
        encoding="utf-8",
        newline="\n",
    )
    return report
