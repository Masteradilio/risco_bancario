from dataclasses import fields, replace
from datetime import date
from decimal import Decimal

import pytest

from src.domain.exceptions import DomainValidationError, TemporalConsistencyError
from src.regulatory.doc3040 import (
    FIELD_CATALOG,
    Accounting4966,
    AdditionalInformation,
    Aggregation,
    Client,
    ConnectedIpoc,
    ConnectedIpocGroup,
    Doc3040Input,
    Guarantee,
    Header,
    MaturityValue,
    Operation,
    RecognizedLoss,
    Requirement,
    SicorInformation,
    SourceRef,
    StageAllocation,
    assert_catalog_covers_models,
    catalog_fields_for,
    iter_sourced_values,
    sourced,
)
from src.regulatory.doc3040 import contract as contract_module


def sv(value, field: str = "field"):
    return sourced(value, system="synthetic_core", field=field, evidence_id=f"EV-{field}")


def header(**changes) -> Header:
    values = {
        "reference_month": sv(date(2026, 7, 1), "reference_month"),
        "reporting_entity_cnpj": sv("12345678", "entity_cnpj"),
        "part": sv(1, "part"),
        "remittance": sv(1, "remittance"),
        "file_type": sv("F", "file_type"),
        "responsible_name": sv("Pessoa Responsavel", "responsible_name"),
        "responsible_email": sv("responsavel@example.test", "responsible_email"),
        "responsible_phone": sv("1133334444", "responsible_phone"),
        "total_clients": sv(1, "total_clients"),
        "expected_loss_methodology": sv("C", "methodology"),
        "differentiated_eir_method": sv("N", "differentiated_eir"),
        "fund_type": None,
    }
    values.update(changes)
    return Header(**values)


def operation(**changes) -> Operation:
    values = {
        "detailed_client": None,
        "ipoc": sv("123456780203112345678901CONTRATO1", "ipoc"),
        "contract_code": sv("CONTRATO1", "contract_code"),
        "modality": sv("0203", "modality"),
        "cosif_accounts": sv("1234567890", "cosif_accounts"),
        "resource_origin": sv("0101", "resource_origin"),
        "indexer": sv("01", "indexer"),
        "indexer_percentage": sv(Decimal("100.0000000"), "indexer_percentage"),
        "currency_variation": sv("790", "currency_variation"),
        "postal_code": sv("01310100", "postal_code"),
        "effective_annual_rate": sv(Decimal("12.5000000"), "effective_rate"),
        "contract_date": sv(date(2025, 1, 15), "contract_date"),
        "contracted_amount": sv(Decimal("1000.00"), "contracted_amount"),
        "nature": sv("01", "nature"),
        "maturity_date": sv(date(2027, 1, 15), "maturity_date"),
        "provision": sv(Decimal("20.00"), "provision"),
        "days_past_due": None,
        "special_characteristics": None,
        "next_installment_date": None,
        "next_installment_amount": None,
        "installment_count": sv(24, "installment_count"),
        "maturities": (
            MaturityValue(
                vertex=sv("v110", "vertex"), amount=sv(Decimal("980.00"), "maturity_amount")
            ),
        ),
        "guarantees": (),
        "additional_information": (),
        "sicor": None,
        "accounting_4966": None,
    }
    values.update(changes)
    return Operation(**values)


def client(op: Operation | None = None, **changes) -> Client:
    values = {
        "code": sv("12345678901", "client_code"),
        "client_type": sv("1", "client_type"),
        "authorization": sv("S", "authorization"),
        "client_size": sv("1", "client_size"),
        "control_type": None,
        "relationship_start": sv(date(2020, 1, 15), "relationship_start"),
        "income": sv(Decimal("5000.00"), "income"),
        "economic_group": None,
        "foreign_name": None,
        "foreign_id_type": None,
        "foreign_id": None,
        "leader_cnpj": None,
        "country_code": None,
        "operations": (op or operation(),),
    }
    values.update(changes)
    return Client(**values)


def document(**changes) -> Doc3040Input:
    values = {
        "header": header(),
        "clients": (client(),),
        "aggregations": (),
        "connected_ipoc_groups": (),
    }
    values.update(changes)
    return Doc3040Input(**values)


def aggregation(**changes) -> Aggregation:
    values = {
        "nature": sv("01"),
        "modality": sv("0203"),
        "resource_origin": sv("0101"),
        "foreign_currency_link": sv("N"),
        "value_band": sv("1"),
        "location": sv("01310"),
        "client_type": sv("1"),
        "control_type": None,
        "performance": sv("01"),
        "special_characteristic": None,
        "provision": sv(Decimal("10")),
        "operation_count": sv(1),
        "client_count": sv(1),
        "maturities": (MaturityValue(vertex=sv("v110"), amount=sv(Decimal("100"))),),
    }
    values.update(changes)
    return Aggregation(**values)


def test_doc3040_layout_001_accepts_explicit_sourced_contract() -> None:
    contract = document()
    lineage = dict(iter_sourced_values(contract))
    assert lineage["header.reporting_entity_cnpj"].origin.field == "entity_cnpj"
    assert lineage["clients[0].operations[0].postal_code"].origin.evidence_id == "EV-postal_code"
    assert all(value.origin.system for value in lineage.values())


def test_doc3040_layout_001_catalog_covers_every_scalar_and_declares_domains_formats() -> None:
    assert_catalog_covers_models()
    assert len(FIELD_CATALOG) >= 90
    assert all(spec.format and spec.requirement for spec in FIELD_CATALOG)
    assert next(spec for spec in FIELD_CATALOG if spec.field == "client_size").domain.startswith(
        "Anexo 24"
    )
    conditional = [spec for spec in FIELD_CATALOG if spec.requirement == Requirement.CONDITIONAL]
    assert conditional and all(spec.condition for spec in conditional)


def test_required_regulatory_scalars_have_no_constructor_defaults() -> None:
    for model in (Header, Client, Operation):
        assert all(field.default is field.default_factory for field in fields(model))
    values = {field.name: getattr(operation(), field.name) for field in fields(Operation)}
    del values["postal_code"]
    with pytest.raises(TypeError, match="postal_code"):
        Operation(**values)


def test_lineage_rejects_blank_source_metadata() -> None:
    with pytest.raises(DomainValidationError, match="source system"):
        SourceRef(system="", field="postal_code", evidence_id="EV-1")


@pytest.mark.parametrize("missing", ["postal_code", "cosif_accounts", "contract_date"])
def test_no_silent_postal_code_cosif_or_contract_date(missing: str) -> None:
    values = {field.name: getattr(operation(), field.name) for field in fields(Operation)}
    del values[missing]
    with pytest.raises(TypeError, match=missing):
        Operation(**values)


def test_pj_requires_control_type_and_detailed_client() -> None:
    with pytest.raises(DomainValidationError, match="control_type"):
        client(client_type=sv("2", "client_type"))
    with pytest.raises(DomainValidationError, match="detailed_client"):
        client(client_type=sv("2", "client_type"), control_type=sv("01", "control_type"))


def test_conditional_groups_and_overdue_information_fail_closed() -> None:
    with pytest.raises(DomainValidationError, match="next installment"):
        operation(next_installment_date=sv(date(2026, 8, 1), "next_installment_date"))
    overdue = MaturityValue(vertex=sv("v205", "vertex"), amount=sv(Decimal("10"), "amount"))
    with pytest.raises(DomainValidationError, match="days_past_due"):
        operation(maturities=(overdue,))


def test_dates_and_totals_must_reconcile() -> None:
    with pytest.raises(TemporalConsistencyError, match="maturity_date"):
        operation(maturity_date=sv(date(2024, 1, 1), "maturity_date"))
    with pytest.raises(DomainValidationError, match="total_clients"):
        document(header=header(total_clients=sv(2, "total_clients")))
    with pytest.raises(TemporalConsistencyError, match="relationship_start"):
        document(clients=(client(relationship_start=sv(date(2026, 7, 1), "relationship_start")),))


def test_header_does_not_invent_methodology_for_funds() -> None:
    with pytest.raises(DomainValidationError, match="required without fund_type"):
        header(expected_loss_methodology=None)
    fund = header(
        fund_type=sv("36", "fund_type"),
        expected_loss_methodology=None,
        differentiated_eir_method=None,
    )
    assert fund.fund_type is not None
    with pytest.raises(DomainValidationError, match="exclusive"):
        replace(fund, expected_loss_methodology=sv("C", "methodology"))


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"reference_month": sv(date(2026, 7, 2))}, "first day"),
        ({"reporting_entity_cnpj": sv("123")}, "exactly 8"),
        ({"part": sv(0)}, "must be positive"),
        ({"remittance": sv(0)}, "must be positive"),
        ({"total_clients": sv(-1)}, "non-negative"),
        ({"responsible_name": sv("")}, "non-empty trimmed"),
        ({"responsible_email": sv("invalid")}, "invalid format"),
        ({"responsible_phone": sv("phone")}, "invalid format"),
    ],
)
def test_header_scalar_formats_fail_closed(changes: dict, message: str) -> None:
    with pytest.raises(DomainValidationError, match=message):
        header(**changes)


def test_maturity_and_operation_scalar_invariants_fail_closed() -> None:
    with pytest.raises(DomainValidationError, match="vCOD"):
        MaturityValue(vertex=sv("110"), amount=sv(Decimal("1")))
    with pytest.raises(DomainValidationError, match="non-negative"):
        MaturityValue(vertex=sv("v110"), amount=sv(Decimal("-1")))
    with pytest.raises(DomainValidationError, match="exactly 8"):
        operation(postal_code=sv("123"))
    with pytest.raises(DomainValidationError, match="non-negative"):
        operation(provision=sv(Decimal("-1")))
    with pytest.raises(DomainValidationError, match="non-negative"):
        operation(contracted_amount=sv(Decimal("-1")))
    duplicate = MaturityValue(vertex=sv("v110"), amount=sv(Decimal("1")))
    with pytest.raises(DomainValidationError, match="vertices must be unique"):
        operation(maturities=(duplicate, duplicate))
    assert operation(contracted_amount=None, maturity_date=None).contracted_amount is None


def test_guarantee_and_additional_information_invariants() -> None:
    common = {
        "status": None,
        "guarantee_type": sv("0101"),
        "identification": None,
        "value_type": sv("01"),
        "percentage": None,
        "original_value": None,
        "revalued_value": None,
        "revalued_percentage": None,
        "revaluation_date": None,
        "sharing": None,
    }
    with pytest.raises(DomainValidationError, match="percentage or original_value"):
        Guarantee(**common)
    with pytest.raises(DomainValidationError, match="cannot exceed 100"):
        Guarantee(**{**common, "percentage": sv(Decimal("101"))})
    with pytest.raises(DomainValidationError, match="revalued value"):
        Guarantee(
            **{
                **common,
                "original_value": sv(Decimal("100")),
                "revaluation_date": sv(date(2026, 7, 1)),
            }
        )
    valid = Guarantee(
        **{
            **common,
            "original_value": sv(Decimal("100")),
            "revalued_percentage": sv(Decimal("80")),
            "revaluation_date": sv(date(2026, 7, 1)),
        }
    )
    assert valid.revalued_percentage is not None

    empty = {
        "information_type": sv("0101"),
        "code": None,
        "identification": None,
        "amount": None,
        "percentage": None,
        "quantity": None,
    }
    with pytest.raises(DomainValidationError, match="requires a sourced payload"):
        AdditionalInformation(**empty)
    assert AdditionalInformation(**{**empty, "code": sv("CODE")}).code is not None


def test_sicor_accounting_and_stage_invariants() -> None:
    sicor = {
        "bacen_reference": sv("12345678901"),
        "destination_order": sv(1),
        "average_total_balance": sv(Decimal("100")),
        "average_outstanding_balance": sv(Decimal("80")),
        "status": sv("01"),
        "bonus_type": None,
        "bonus_amount": None,
        "bonus_payment_date": None,
    }
    with pytest.raises(DomainValidationError, match="destination_order"):
        SicorInformation(**{**sicor, "destination_order": sv(0)})
    with pytest.raises(DomainValidationError, match="complete conditional group"):
        SicorInformation(**{**sicor, "bonus_type": sv("01")})
    assert SicorInformation(**sicor).bonus_type is None

    with pytest.raises(DomainValidationError, match="first day"):
        StageAllocation(reason=sv("001"), allocation_month=sv(date(2026, 7, 2)))
    allocation = StageAllocation(reason=sv("001"), allocation_month=sv(date(2026, 7, 1)))
    RecognizedLoss(reason=sv("01"), amount=sv(Decimal("1")))
    empty_accounting = {
        "asset_classification": None,
        "stage": None,
        "instrument_quantity": None,
        "gross_carrying_amount": None,
        "accumulated_loss": None,
        "fair_value": None,
        "effective_interest_rate": None,
        "monthly_income": None,
        "stage_one_pd_type": None,
        "minimum_provision_portfolio": None,
        "isolated_credit_risk_treatment": None,
        "stage_allocations": (),
        "recognized_losses": (),
    }
    with pytest.raises(DomainValidationError, match="must contain"):
        Accounting4966(**empty_accounting)
    with pytest.raises(DomainValidationError, match="requires gross"):
        Accounting4966(**{**empty_accounting, "accumulated_loss": sv(Decimal("1"))})
    with pytest.raises(DomainValidationError, match="explicit sourced stage"):
        Accounting4966(**{**empty_accounting, "stage_allocations": (allocation,)})
    valid = Accounting4966(
        **{
            **empty_accounting,
            "stage": sv("1"),
            "gross_carrying_amount": sv(Decimal("100")),
            "accumulated_loss": sv(Decimal("1")),
            "stage_allocations": (allocation,),
        }
    )
    assert valid.stage is not None


def test_client_group_aggregation_and_document_invariants() -> None:
    with pytest.raises(DomainValidationError, match="at least one operation"):
        client(operations=())
    connected = ConnectedIpoc(ipoc=operation().ipoc)
    with pytest.raises(DomainValidationError, match="at least two unique"):
        ConnectedIpocGroup(ipocs=(connected,))
    with pytest.raises(DomainValidationError, match="at least two unique"):
        ConnectedIpocGroup(ipocs=(connected, connected))

    with pytest.raises(DomainValidationError, match="PJ aggregations"):
        aggregation(client_type=sv("2"))
    with pytest.raises(DomainValidationError, match="counts must be positive"):
        aggregation(operation_count=sv(0))
    with pytest.raises(DomainValidationError, match="requires sourced maturity"):
        aggregation(maturities=())

    with pytest.raises(DomainValidationError, match="individualized clients or aggregations"):
        document(clients=(), aggregations=(), header=header(total_clients=sv(0)))
    original = client()
    with pytest.raises(DomainValidationError, match="client codes must be unique"):
        document(clients=(original, original), header=header(total_clients=sv(2)))
    second_op = operation(ipoc=sv("123456780203112345678901CONTRATO2"))
    with pytest.raises(DomainValidationError, match="operation IPOCs must be unique"):
        document(clients=(client(), client(code=sv("OTHER"))), header=header(total_clients=sv(2)))
    with pytest.raises(DomainValidationError, match="cannot be lower"):
        document(aggregations=(aggregation(),), header=header(total_clients=sv(0)))
    group = ConnectedIpocGroup(
        ipocs=(
            ConnectedIpoc(ipoc=operation().ipoc),
            ConnectedIpoc(ipoc=second_op.ipoc),
        )
    )
    with pytest.raises(DomainValidationError, match="must exist"):
        document(connected_ipoc_groups=(group,))
    two_operations = replace(client(), operations=(operation(), second_op))
    assert document(
        clients=(two_operations,), connected_ipoc_groups=(group, group)
    ).connected_ipoc_groups
    assert operation(cosif_accounts=None).cosif_accounts is None


def test_catalog_query_and_completeness_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    assert catalog_fields_for(Header)
    monkeypatch.setattr(
        contract_module,
        "FIELD_CATALOG",
        tuple(
            spec
            for spec in contract_module.FIELD_CATALOG
            if not (spec.model == "Header" and spec.field == "responsible_name")
        ),
    )
    with pytest.raises(AssertionError, match="catalog is incomplete"):
        assert_catalog_covers_models()
