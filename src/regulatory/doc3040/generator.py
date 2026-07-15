"""Deterministic XML candidate generation for the Document 3040 pre-validator."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any
from xml.etree import ElementTree as ET

from ...domain.exceptions import DomainValidationError
from .contract import (
    Accounting4966,
    AdditionalInformation,
    Aggregation,
    Client,
    Doc3040Input,
    Guarantee,
    Header,
    MaturityValue,
    Operation,
    RecognizedLoss,
    SicorInformation,
    SourcedValue,
    StageAllocation,
)
from .layout_registry import LayoutVersion, layout_for_reference_month


@dataclass(frozen=True, slots=True)
class XmlCandidate:
    content: bytes
    sha256: str
    layout_version: str
    interface_label: str
    validation_status: str
    total_clients: int
    total_operations: int


def _v[T](item: SourcedValue[T]) -> T:
    return item.value


def _month(value: date) -> str:
    return value.strftime("%Y-%m")


def _day(value: date) -> str:
    return value.isoformat()


def _number(value: Decimal | int, places: int | None = None) -> str:
    if isinstance(value, int):
        return str(value)
    if places is not None:
        quantum = Decimal(1).scaleb(-places)
        value = value.quantize(quantum, rounding=ROUND_HALF_EVEN)
    return format(value, "f")


def compose_ipoc(header: Header, client: Client, operation: Operation) -> str:
    """Compose the official IPOC components for a newly reported operation."""

    client_type = _v(client.client_type)
    client_code = _v(client.code)
    if client_type == "1":
        if len(client_code) != 11:
            raise DomainValidationError("PF IPOC component requires an 11-position CPF")
        component = client_code
    elif client_type == "2":
        if len(client_code) < 8:
            raise DomainValidationError("PJ IPOC component requires the 8-position CNPJ root")
        component = client_code[:8]
    elif client_type in {"3", "4", "5", "6"}:
        if len(client_code) > 14:
            raise DomainValidationError("other-client IPOC component cannot exceed 14 positions")
        component = client_code.zfill(14)
    else:
        raise DomainValidationError(f"unsupported client type {client_type} for IPOC")
    return "".join(
        (
            _v(header.reporting_entity_cnpj),
            _v(operation.modality),
            client_type,
            component,
            _v(operation.contract_code),
        )
    )


def _set_optional(
    element: ET.Element,
    attribute: str,
    item: SourcedValue[Any] | None,
    formatter: Callable[[Any], str] = str,
) -> None:
    if item is not None:
        element.set(attribute, formatter(item.value))


def _maturities(parent: ET.Element, values: tuple[MaturityValue, ...]) -> None:
    if not values:
        return
    element = ET.SubElement(parent, "Venc")
    for maturity in sorted(values, key=lambda item: int(_v(item.vertex)[1:])):
        element.set(_v(maturity.vertex), _number(_v(maturity.amount), 2))


def _guarantee(parent: ET.Element, value: Guarantee) -> None:
    element = ET.SubElement(parent, "Gar")
    _set_optional(element, "SitGar", value.status)
    element.set("Tp", _v(value.guarantee_type))
    _set_optional(element, "Ident", value.identification)
    element.set("TpVlrGar", _v(value.value_type))
    _set_optional(element, "PercGar", value.percentage, lambda x: _number(x, 2))
    _set_optional(element, "VlrOrig", value.original_value, lambda x: _number(x, 2))
    _set_optional(element, "VlrData", value.revalued_value, lambda x: _number(x, 2))
    _set_optional(element, "PercData", value.revalued_percentage, lambda x: _number(x, 2))
    _set_optional(element, "DtReav", value.revaluation_date, _day)
    _set_optional(element, "Compart", value.sharing)


def _additional(parent: ET.Element, value: AdditionalInformation) -> None:
    element = ET.SubElement(parent, "Inf")
    element.set("Tp", _v(value.information_type))
    _set_optional(element, "Cd", value.code)
    _set_optional(element, "Ident", value.identification)
    _set_optional(element, "Valor", value.amount, lambda x: _number(x, 2))
    _set_optional(element, "Perc", value.percentage, lambda x: _number(x, 2))
    _set_optional(element, "Qtd", value.quantity)


def _sicor(parent: ET.Element, value: SicorInformation) -> None:
    element = ET.SubElement(parent, "Sicor")
    element.set("RefBacen", _v(value.bacen_reference))
    element.set("Ordem", str(_v(value.destination_order)))
    element.set("VlrSaldoTot", _number(_v(value.average_total_balance), 2))
    element.set("VlrSaldoVinc", _number(_v(value.average_outstanding_balance), 2))
    element.set("Situacao", _v(value.status))
    _set_optional(element, "TpBonusRebate", value.bonus_type)
    _set_optional(element, "VlrBonusRebate", value.bonus_amount, lambda x: _number(x, 2))
    _set_optional(element, "DtBonusRebate", value.bonus_payment_date, _day)


def _stage(parent: ET.Element, value: StageAllocation) -> None:
    element = ET.SubElement(parent, "Estagio")
    element.set("Motivo", _v(value.reason))
    element.set("DtAlocacao", _month(_v(value.allocation_month)))


def _loss(parent: ET.Element, value: RecognizedLoss) -> None:
    element = ET.SubElement(parent, "Perda")
    element.set("MotPerda", _v(value.reason))
    element.set("VlrPerda", _number(_v(value.amount), 2))


def _accounting(parent: ET.Element, value: Accounting4966) -> None:
    element = ET.SubElement(parent, "ContInstFinRes4966")
    _set_optional(element, "ClasAtFin", value.asset_classification)
    _set_optional(element, "EstInstFin", value.stage)
    _set_optional(element, "QtdInst", value.instrument_quantity)
    _set_optional(element, "VlrContBr", value.gross_carrying_amount, lambda x: _number(x, 2))
    _set_optional(element, "VlrPerdaAcum", value.accumulated_loss, lambda x: _number(x, 2))
    _set_optional(element, "VlrJusto", value.fair_value, lambda x: _number(x, 2))
    _set_optional(element, "TJE", value.effective_interest_rate, lambda x: _number(x, 7))
    _set_optional(element, "RendMes", value.monthly_income, lambda x: _number(x, 2))
    _set_optional(element, "PdEst1", value.stage_one_pd_type)
    _set_optional(element, "CartProvMin", value.minimum_provision_portfolio)
    _set_optional(element, "TratRisc", value.isolated_credit_risk_treatment)
    for allocation in value.stage_allocations:
        _stage(element, allocation)
    for loss in value.recognized_losses:
        _loss(element, loss)


def _operation(parent: ET.Element, header: Header, client: Client, value: Operation) -> None:
    expected_ipoc = compose_ipoc(header, client, value)
    if _v(value.ipoc) != expected_ipoc:
        raise DomainValidationError(
            f"IPOC does not reconcile to current reported components; expected {expected_ipoc}"
        )
    if value.cosif_accounts is not None:
        raise DomainValidationError(
            "Cosif is discontinued and prohibited for the supported 2026 layout"
        )
    element = ET.SubElement(parent, "Op")
    _set_optional(element, "DetCli", value.detailed_client)
    element.set("IPOC", _v(value.ipoc))
    element.set("Contrt", _v(value.contract_code))
    element.set("Mod", _v(value.modality))
    element.set("OrigemRec", _v(value.resource_origin))
    element.set("Indx", _v(value.indexer))
    element.set("PercIndx", _number(_v(value.indexer_percentage), 7))
    element.set("VarCamb", _v(value.currency_variation))
    element.set("CEP", _v(value.postal_code))
    element.set("TaxEft", _number(_v(value.effective_annual_rate), 7))
    element.set("DtContr", _day(_v(value.contract_date)))
    _set_optional(element, "VlrContr", value.contracted_amount, lambda x: _number(x, 2))
    element.set("NatuOp", _v(value.nature))
    _set_optional(element, "DtVencOp", value.maturity_date, _day)
    element.set("ProvConsttd", _number(_v(value.provision), 2))
    _set_optional(element, "DiaAtraso", value.days_past_due)
    _set_optional(element, "CaracEspecial", value.special_characteristics)
    _set_optional(element, "DtaProxParcela", value.next_installment_date, _day)
    _set_optional(element, "VlrProxParcela", value.next_installment_amount, lambda x: _number(x, 2))
    _set_optional(element, "QtdParcelas", value.installment_count)
    _maturities(element, value.maturities)
    for guarantee in value.guarantees:
        _guarantee(element, guarantee)
    for information in value.additional_information:
        _additional(element, information)
    if value.sicor is not None:
        _sicor(element, value.sicor)
    if value.accounting_4966 is not None:
        _accounting(element, value.accounting_4966)


def _client(parent: ET.Element, header: Header, value: Client) -> None:
    element = ET.SubElement(parent, "Cli")
    element.set("Cd", _v(value.code))
    element.set("Tp", _v(value.client_type))
    element.set("Autorzc", _v(value.authorization))
    element.set("PorteCli", _v(value.client_size))
    _set_optional(element, "TpCtrl", value.control_type)
    element.set("IniRelactCli", _day(_v(value.relationship_start)))
    element.set("FatAnual", _number(_v(value.income), 2))
    _set_optional(element, "CongEcon", value.economic_group)
    _set_optional(element, "NomeCli", value.foreign_name)
    _set_optional(element, "TpIdentExt", value.foreign_id_type)
    _set_optional(element, "CodExt", value.foreign_id)
    _set_optional(element, "IdLiderBR", value.leader_cnpj)
    _set_optional(element, "IdPais", value.country_code)
    for operation in value.operations:
        _operation(element, header, value, operation)


def _aggregation(parent: ET.Element, value: Aggregation) -> None:
    element = ET.SubElement(parent, "Agreg")
    for attribute, item in (
        ("NatuOp", value.nature),
        ("Mod", value.modality),
        ("OrigemRec", value.resource_origin),
        ("VincME", value.foreign_currency_link),
        ("FaixaVlr", value.value_band),
        ("Localiz", value.location),
        ("TpCli", value.client_type),
        ("DesempOp", value.performance),
    ):
        element.set(attribute, _v(item))
    _set_optional(element, "TpCtrl", value.control_type)
    _set_optional(element, "CaracEspecial", value.special_characteristic)
    element.set("ProvConsttd", _number(_v(value.provision), 2))
    element.set("QtdOp", str(_v(value.operation_count)))
    element.set("QtdCli", str(_v(value.client_count)))
    _maturities(element, value.maturities)


def _root(contract: Doc3040Input) -> ET.Element:
    header = contract.header
    element = ET.Element("Doc3040")
    element.set("DtBase", _month(_v(header.reference_month)))
    element.set("CNPJ", _v(header.reporting_entity_cnpj))
    element.set("Remessa", str(_v(header.remittance)))
    element.set("Parte", str(_v(header.part)))
    _set_optional(element, "TpArq", header.file_type)
    element.set("NomeResp", _v(header.responsible_name))
    element.set("EmailResp", _v(header.responsible_email))
    element.set("TelResp", _v(header.responsible_phone))
    element.set("TotalCli", str(_v(header.total_clients)))
    _set_optional(element, "MetodApPE", header.expected_loss_methodology)
    _set_optional(element, "MetodDifTJE", header.differentiated_eir_method)
    _set_optional(element, "TpFundo", header.fund_type)
    for client in contract.clients:
        _client(element, header, client)
    for aggregation in contract.aggregations:
        _aggregation(element, aggregation)
    for group in contract.connected_ipoc_groups:
        group_element = ET.SubElement(element, "ConIpocs")
        for connected in group.ipocs:
            ET.SubElement(group_element, "ipocCon", {"ipoc": _v(connected.ipoc)})
    return element


def generate_xml_candidate(
    contract: Doc3040Input, layout: LayoutVersion | None = None
) -> XmlCandidate:
    """Render a deterministic candidate; this does not claim XSD/critic validity."""

    selected = layout or layout_for_reference_month(_v(contract.header.reference_month))
    if not (selected.effective_from <= _v(contract.header.reference_month) < selected.effective_to):
        raise DomainValidationError("selected layout does not cover the contract reference month")
    ET.indent(root := _root(contract), space="  ")
    content = ET.tostring(root, encoding="utf-8", xml_declaration=True, short_empty_elements=True)
    return XmlCandidate(
        content=content,
        sha256=hashlib.sha256(content).hexdigest(),
        layout_version=selected.version,
        interface_label="pre-validator",
        validation_status="XSD_AND_CRITICS_PENDING",
        total_clients=_v(contract.header.total_clients),
        total_operations=sum(len(client.operations) for client in contract.clients),
    )
