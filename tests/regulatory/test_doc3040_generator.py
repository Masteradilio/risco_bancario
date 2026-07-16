from dataclasses import replace
from datetime import date
from decimal import Decimal
from xml.etree import ElementTree as ET

import pytest

from src.domain.exceptions import DomainValidationError
from src.regulatory.doc3040 import (
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
    SicorInformation,
    StageAllocation,
    compose_ipoc,
    generate_xml_candidate,
    load_layout_registry,
    sourced,
)
from src.regulatory.doc3040.generator import _number


def sv(value, field: str):
    return sourced(value, system="synthetic_core", field=field, evidence_id=f"EV-{field}")


def base_operation(**changes) -> Operation:
    values = {
        "detailed_client": None,
        "ipoc": sv("123456780203112345678901CONTRATO1", "ipoc"),
        "contract_code": sv("CONTRATO1", "contract_code"),
        "modality": sv("0203", "modality"),
        "cosif_accounts": None,
        "resource_origin": sv("0101", "resource_origin"),
        "indexer": sv("01", "indexer"),
        "indexer_percentage": sv(Decimal("100"), "indexer_percentage"),
        "currency_variation": sv("790", "currency_variation"),
        "postal_code": sv("01310100", "postal_code"),
        "effective_annual_rate": sv(Decimal("12.5"), "effective_annual_rate"),
        "contract_date": sv(date(2025, 1, 15), "contract_date"),
        "contracted_amount": sv(Decimal("1000"), "contracted_amount"),
        "nature": sv("01", "nature"),
        "maturity_date": sv(date(2027, 1, 15), "maturity_date"),
        "provision": sv(Decimal("20"), "provision"),
        "days_past_due": None,
        "special_characteristics": None,
        "next_installment_date": None,
        "next_installment_amount": None,
        "installment_count": sv(24, "installment_count"),
        "maturities": (
            MaturityValue(vertex=sv("v120", "v120"), amount=sv(Decimal("400"), "m120")),
            MaturityValue(vertex=sv("v110", "v110"), amount=sv(Decimal("580"), "m110")),
        ),
        "guarantees": (),
        "additional_information": (),
        "sicor": None,
        "accounting_4966": None,
    }
    values.update(changes)
    return Operation(**values)


def base_client(operation: Operation | None = None) -> Client:
    return Client(
        code=sv("12345678901", "client_code"),
        client_type=sv("1", "client_type"),
        authorization=sv("S", "authorization"),
        client_size=sv("1", "client_size"),
        control_type=None,
        relationship_start=sv(date(2020, 1, 15), "relationship_start"),
        income=sv(Decimal("5000"), "income"),
        economic_group=None,
        foreign_name=None,
        foreign_id_type=None,
        foreign_id=None,
        leader_cnpj=None,
        country_code=None,
        operations=(operation or base_operation(),),
    )


def base_header() -> Header:
    return Header(
        reference_month=sv(date(2026, 7, 1), "reference_month"),
        reporting_entity_cnpj=sv("12345678", "entity_cnpj"),
        part=sv(1, "part"),
        remittance=sv(1, "remittance"),
        file_type=sv("F", "file_type"),
        responsible_name=sv("Pessoa Responsavel", "responsible_name"),
        responsible_email=sv("responsavel@example.test", "responsible_email"),
        responsible_phone=sv("1133334444", "responsible_phone"),
        total_clients=sv(1, "total_clients"),
        expected_loss_methodology=sv("C", "methodology"),
        differentiated_eir_method=sv("N", "differentiated_eir"),
        fund_type=None,
    )


def base_document(operation: Operation | None = None) -> Doc3040Input:
    return Doc3040Input(
        header=base_header(),
        clients=(base_client(operation),),
        aggregations=(),
        connected_ipoc_groups=(),
    )


def test_doc3040_layout_001_generates_deterministic_candidate_and_totals() -> None:
    first = generate_xml_candidate(base_document())
    second = generate_xml_candidate(base_document())
    assert first.content == second.content
    assert first.sha256 == second.sha256
    assert first.layout_version == "2026.07-observed-20260714"
    assert first.interface_label == "pre-validator"
    assert first.validation_status == "XSD_AND_CRITICS_PENDING"
    assert first.total_clients == 1 and first.total_operations == 1
    root = ET.fromstring(first.content)
    assert root.attrib["TotalCli"] == "1"
    operation = root.find("./Cli/Op")
    assert operation is not None
    assert "Cosif" not in operation.attrib
    assert list(operation.find("Venc").attrib) == ["v110", "v120"]


def test_ipoc_uses_official_components_and_rejects_mismatch() -> None:
    document = base_document()
    operation = document.clients[0].operations[0]
    assert compose_ipoc(document.header, document.clients[0], operation) == operation.ipoc.value
    invalid = replace(operation, ipoc=sv("ARBITRARIO", "ipoc"))
    with pytest.raises(DomainValidationError, match="IPOC does not reconcile"):
        generate_xml_candidate(base_document(invalid))


def test_supported_layout_prohibits_discontinued_cosif() -> None:
    operation = replace(base_operation(), cosif_accounts=sv("1234567890", "cosif"))
    with pytest.raises(DomainValidationError, match="Cosif is discontinued"):
        generate_xml_candidate(base_document(operation))


def test_all_applicable_operation_blocks_use_only_sourced_values() -> None:
    guarantee = Guarantee(
        status=sv("01", "guarantee_status"),
        guarantee_type=sv("0881", "guarantee_type"),
        identification=sv("GAR-1", "guarantee_id"),
        value_type=sv("01", "guarantee_value_type"),
        percentage=None,
        original_value=sv(Decimal("500"), "guarantee_original"),
        revalued_value=sv(Decimal("450"), "guarantee_revalued"),
        revalued_percentage=None,
        revaluation_date=sv(date(2026, 6, 30), "guarantee_date"),
        sharing=sv("01", "guarantee_sharing"),
    )
    information = AdditionalInformation(
        information_type=sv("1408", "information_type"),
        code=None,
        identification=sv("12", "regulatory_use"),
        amount=None,
        percentage=None,
        quantity=None,
    )
    sicor = SicorInformation(
        bacen_reference=sv("12345678901", "sicor_ref"),
        destination_order=sv(1, "sicor_order"),
        average_total_balance=sv(Decimal("980"), "sicor_total"),
        average_outstanding_balance=sv(Decimal("980"), "sicor_outstanding"),
        status=sv("01", "sicor_status"),
        bonus_type=None,
        bonus_amount=None,
        bonus_payment_date=None,
    )
    accounting = Accounting4966(
        asset_classification=sv("1", "asset_classification"),
        stage=sv("2", "stage"),
        instrument_quantity=None,
        gross_carrying_amount=sv(Decimal("980"), "gross_carrying_amount"),
        accumulated_loss=sv(Decimal("20"), "accumulated_loss"),
        fair_value=None,
        effective_interest_rate=sv(Decimal("12.5"), "eir"),
        monthly_income=sv(Decimal("10"), "monthly_income"),
        stage_one_pd_type=None,
        minimum_provision_portfolio=sv("C2", "minimum_portfolio"),
        isolated_credit_risk_treatment=sv("N", "isolated_treatment"),
        stage_allocations=(
            StageAllocation(
                reason=sv("201", "stage_reason"),
                allocation_month=sv(date(2026, 7, 1), "allocation_month"),
            ),
        ),
        recognized_losses=(
            RecognizedLoss(
                reason=sv("01", "loss_reason"), amount=sv(Decimal("7.25"), "recognized_loss")
            ),
        ),
    )
    operation = replace(
        base_operation(),
        guarantees=(guarantee,),
        additional_information=(information,),
        sicor=sicor,
        accounting_4966=accounting,
    )
    root = ET.fromstring(generate_xml_candidate(base_document(operation)).content)
    assert root.find("./Cli/Op/Gar").attrib["VlrData"] == "450.00"
    assert root.find("./Cli/Op/Inf").attrib == {"Tp": "1408", "Ident": "12"}
    assert root.find("./Cli/Op/Sicor").attrib["VlrSaldoTot"] == "980.00"
    accounting_xml = root.find("./Cli/Op/ContInstFinRes4966")
    assert accounting_xml.attrib["VlrPerdaAcum"] == "20.00"
    assert accounting_xml.find("Estagio").attrib["DtAlocacao"] == "2026-07"
    assert accounting_xml.find("Perda").attrib["VlrPerda"] == "7.25"


def test_aggregation_is_rendered_without_inventing_vertices() -> None:
    aggregation = Aggregation(
        nature=sv("01", "aggregate_nature"),
        modality=sv("0203", "aggregate_modality"),
        resource_origin=sv("0100", "aggregate_origin"),
        foreign_currency_link=sv("N", "foreign_currency_link"),
        value_band=sv("4", "value_band"),
        location=sv("35503", "location"),
        client_type=sv("1", "aggregate_client_type"),
        control_type=None,
        performance=sv("01", "performance"),
        special_characteristic=None,
        provision=sv(Decimal("3"), "aggregate_provision"),
        operation_count=sv(2, "operation_count"),
        client_count=sv(2, "client_count"),
        maturities=(
            MaturityValue(
                vertex=sv("v110", "aggregate_vertex"), amount=sv(Decimal("100"), "aggregate_amount")
            ),
        ),
    )
    document = replace(
        base_document(),
        header=replace(base_header(), total_clients=sv(3, "total_clients")),
        aggregations=(aggregation,),
    )
    root = ET.fromstring(generate_xml_candidate(document).content)
    assert root.find("./Agreg").attrib["QtdCli"] == "2"
    assert root.find("./Agreg/Venc").attrib == {"v110": "100.00"}


def test_selected_layout_must_cover_reference_month() -> None:
    layout = replace(
        load_layout_registry()[0],
        effective_from=date(2026, 8, 1),
        effective_to=date(2026, 9, 1),
    )
    with pytest.raises(DomainValidationError, match="does not cover"):
        generate_xml_candidate(base_document(), layout)


def test_number_formatting_and_empty_maturities_are_deterministic() -> None:
    assert _number(2) == "2"
    assert _number(Decimal("2.50")) == "2.50"
    root = ET.fromstring(
        generate_xml_candidate(base_document(base_operation(maturities=()))).content
    )
    assert root.find("./Cli/Op/Venc") is None


def test_ipoc_composition_covers_all_client_types() -> None:
    header = base_header()
    op = base_operation()
    pf = base_client(op)
    with pytest.raises(DomainValidationError, match="11-position CPF"):
        compose_ipoc(header, replace(pf, code=sv("123", "code")), op)

    pj = replace(
        pf,
        code=sv("12345678000199", "code"),
        client_type=sv("2", "type"),
        control_type=sv("01", "control"),
        operations=(replace(op, detailed_client=sv("12345678000199", "detail")),),
    )
    assert "12345678" in compose_ipoc(header, pj, pj.operations[0])
    with pytest.raises(DomainValidationError, match="8-position CNPJ"):
        compose_ipoc(header, replace(pj, code=sv("123", "code")), pj.operations[0])

    other = replace(pf, code=sv("123", "code"), client_type=sv("3", "type"))
    assert "00000000000123" in compose_ipoc(header, other, op)
    object.__setattr__(other.code, "value", "1" * 15)
    with pytest.raises(DomainValidationError, match="cannot exceed 14"):
        compose_ipoc(header, other, op)
    with pytest.raises(DomainValidationError, match="unsupported client type"):
        compose_ipoc(header, replace(pf, client_type=sv("9", "type")), op)


def test_connected_ipoc_groups_are_rendered() -> None:
    first = base_operation()
    second = replace(
        first,
        contract_code=sv("CONTRATO2", "contract_code"),
        ipoc=sv("123456780203112345678901CONTRATO2", "ipoc"),
    )
    client = replace(base_client(), operations=(first, second))
    group = ConnectedIpocGroup(
        ipocs=(ConnectedIpoc(ipoc=first.ipoc), ConnectedIpoc(ipoc=second.ipoc))
    )
    contract = replace(base_document(), clients=(client,), connected_ipoc_groups=(group,))
    root = ET.fromstring(generate_xml_candidate(contract).content)
    assert [item.attrib["ipoc"] for item in root.findall("./ConIpocs/ipocCon")] == [
        first.ipoc.value,
        second.ipoc.value,
    ]
