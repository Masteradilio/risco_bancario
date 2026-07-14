from dataclasses import fields, replace
from datetime import date
from decimal import Decimal

import pytest

from src.domain.exceptions import DomainValidationError, TemporalConsistencyError
from src.regulatory.doc3040 import (
    FIELD_CATALOG,
    Client,
    Doc3040Input,
    Header,
    MaturityValue,
    Operation,
    Requirement,
    SourceRef,
    assert_catalog_covers_models,
    iter_sourced_values,
    sourced,
)


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
