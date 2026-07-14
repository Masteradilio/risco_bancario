"""Fail-closed input contract for the SCR Document 3040 pre-validator.

No regulatory scalar has a default. A present value always carries lineage; an
optional or conditional field must be passed explicitly as a sourced value or
``None``. Domain contents are bound to reference dates by the layout registry.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, fields, is_dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum

from ...domain.exceptions import DomainValidationError, TemporalConsistencyError


class Requirement(StrEnum):
    REQUIRED = "required"
    CONDITIONAL = "conditional"
    OPTIONAL = "optional"


@dataclass(frozen=True, slots=True, kw_only=True)
class SourceRef:
    system: str
    field: str
    evidence_id: str

    def __post_init__(self) -> None:
        for name in ("system", "field", "evidence_id"):
            value = getattr(self, name)
            if not value or value != value.strip():
                raise DomainValidationError(f"source {name} must be a non-empty trimmed string")


@dataclass(frozen=True, slots=True, kw_only=True)
class SourcedValue[T]:
    value: T
    origin: SourceRef


@dataclass(frozen=True, slots=True)
class FieldSpec:
    model: str
    field: str
    xml_element: str
    xml_attribute: str | None
    format: str
    requirement: Requirement
    domain: str | None = None
    condition: str | None = None


def _s(
    model: str,
    field: str,
    element: str,
    attribute: str | None,
    format_: str,
    requirement: Requirement,
    domain: str | None = None,
    condition: str | None = None,
) -> FieldSpec:
    return FieldSpec(model, field, element, attribute, format_, requirement, domain, condition)


R = Requirement.REQUIRED
C = Requirement.CONDITIONAL
OPTIONAL = Requirement.OPTIONAL

# Official BCB SCR3040 layout fields represented by this contract. The source was
# consulted on 2026-07-14; version/date selection is intentionally deferred to 12.2.
FIELD_CATALOG: tuple[FieldSpec, ...] = (
    _s("Header", "reference_month", "Doc3040", "DtBase", "AAAA-MM", R),
    _s("Header", "reporting_entity_cnpj", "Doc3040", "CNPJ", "A8", R),
    _s("Header", "part", "Doc3040", "Parte", "N", R),
    _s("Header", "remittance", "Doc3040", "Remessa", "N", R),
    _s(
        "Header",
        "file_type",
        "Doc3040",
        "TpArq",
        "A1",
        C,
        "Anexo 15",
        "required unless BCB-authorized partitioning applies",
    ),
    _s("Header", "responsible_name", "Doc3040", "NomeResp", "A", R),
    _s("Header", "responsible_email", "Doc3040", "EmailResp", "A", R),
    _s("Header", "responsible_phone", "Doc3040", "TelResp", "A", R),
    _s("Header", "total_clients", "Doc3040", "TotalCli", "N", R),
    _s(
        "Header",
        "expected_loss_methodology",
        "Doc3040",
        "MetodApPE",
        "A1",
        C,
        "Anexo 39",
        "required when fund_type is absent",
    ),
    _s(
        "Header",
        "differentiated_eir_method",
        "Doc3040",
        "MetodDifTJE",
        "A1",
        C,
        "S/N",
        "required when fund_type is absent",
    ),
    _s(
        "Header",
        "fund_type",
        "Doc3040",
        "TpFundo",
        "A2",
        C,
        "36/46/41/44",
        "exclusive and required for FIDC or SEP",
    ),
    _s("Client", "code", "Cli", "Cd", "A14", R),
    _s("Client", "client_type", "Cli", "Tp", "A1", R, "Anexo 11"),
    _s("Client", "authorization", "Cli", "Autorzc", "A1", R, "Anexo 20"),
    _s("Client", "client_size", "Cli", "PorteCli", "A1", R, "Anexo 24 (PJ) / Anexo 25 (PF)"),
    _s("Client", "control_type", "Cli", "TpCtrl", "A1", C, "Anexo 10", "required for PJ"),
    _s("Client", "relationship_start", "Cli", "IniRelactCli", "AAAA-MM-DD", R),
    _s(
        "Client",
        "income",
        "Cli",
        "FatAnual",
        "N19,2",
        R,
        condition="annual revenue for PJ; monthly income for PF",
    ),
    _s("Client", "economic_group", "Cli", "CongEcon", "A40", OPTIONAL),
    _s("Client", "foreign_name", "Cli", "NomeCli", "A40", C, condition="foreign client"),
    _s("Client", "foreign_id_type", "Cli", "TpIdentExt", "A2", C, "Anexo 29", "foreign client"),
    _s("Client", "foreign_id", "Cli", "CodExt", "A20", C, condition="foreign client"),
    _s("Client", "leader_cnpj", "Cli", "IdLiderBR", "A8", C, condition="Brazilian group leader"),
    _s("Client", "country_code", "Cli", "IdPais", "A3", C, "Anexo 30", "foreign group/client"),
    _s("Operation", "detailed_client", "Op", "DetCli", "A14", C, condition="required for PJ"),
    _s("Operation", "ipoc", "Op", "IPOC", "A67", R),
    _s("Operation", "contract_code", "Op", "Contrt", "A40", R),
    _s("Operation", "modality", "Op", "Mod", "A4", R, "Anexo 3"),
    _s("Operation", "cosif_accounts", "Op", "Cosif", "A255", R),
    _s("Operation", "resource_origin", "Op", "OrigemRec", "A4", R, "Anexo 4"),
    _s("Operation", "indexer", "Op", "Indx", "A2", R, "Anexo 5"),
    _s("Operation", "indexer_percentage", "Op", "PercIndx", "N11,7", R),
    _s("Operation", "currency_variation", "Op", "VarCamb", "A3", R, "Anexo 6"),
    _s("Operation", "postal_code", "Op", "CEP", "A8", R),
    _s("Operation", "effective_annual_rate", "Op", "TaxEft", "N11,7", R),
    _s("Operation", "contract_date", "Op", "DtContr", "AAAA-MM-DD", R),
    _s(
        "Operation",
        "contracted_amount",
        "Op",
        "VlrContr",
        "N19,2",
        C,
        condition="modality and operation rules",
    ),
    _s("Operation", "nature", "Op", "NatuOp", "A2", R, "Anexo 2"),
    _s(
        "Operation",
        "maturity_date",
        "Op",
        "DtVencOp",
        "AAAA-MM-DD",
        OPTIONAL,
        condition="absence means indeterminate maturity",
    ),
    _s("Operation", "provision", "Op", "ProvConsttd", "N19,2", R),
    _s(
        "Operation",
        "days_past_due",
        "Op",
        "DiaAtraso",
        "N6",
        C,
        condition="maturity vertices 205 through 330",
    ),
    _s(
        "Operation",
        "special_characteristics",
        "Op",
        "CaracEspecial",
        "A40",
        OPTIONAL,
        "Anexo 8",
    ),
    _s(
        "Operation",
        "next_installment_date",
        "Op",
        "DtaProxParcela",
        "AAAA-MM-DD",
        C,
        condition="next installment exists",
    ),
    _s(
        "Operation",
        "next_installment_amount",
        "Op",
        "VlrProxParcela",
        "N19,2",
        C,
        condition="next installment exists",
    ),
    _s("Operation", "installment_count", "Op", "QtdParcelas", "N4", OPTIONAL),
    _s("MaturityValue", "vertex", "Venc", "vCOD", "A4", R, "Anexo 1"),
    _s("MaturityValue", "amount", "Venc", "vCOD", "N19,2", R),
    _s("Guarantee", "status", "Gar", "SitGar", "A2", C, "Anexo 47", "guarantee rules"),
    _s("Guarantee", "guarantee_type", "Gar", "Tp", "A2+A2", R, "Anexo 12"),
    _s("Guarantee", "identification", "Gar", "Ident", "A21", C, condition="guarantee subtype"),
    _s("Guarantee", "value_type", "Gar", "TpVlrGar", "A2", R, "Anexo 48"),
    _s("Guarantee", "percentage", "Gar", "PercGar", "N5,2", C, condition="personal guarantee"),
    _s(
        "Guarantee",
        "original_value",
        "Gar",
        "VlrOrig",
        "N19,2",
        C,
        condition="non-personal guarantee",
    ),
    _s("Guarantee", "revalued_value", "Gar", "VlrData", "N19,2", C, condition="revalued guarantee"),
    _s(
        "Guarantee",
        "revalued_percentage",
        "Gar",
        "PercData",
        "N5,2",
        C,
        condition="revalued guarantee",
    ),
    _s(
        "Guarantee",
        "revaluation_date",
        "Gar",
        "DtReav",
        "AAAA-MM-DD",
        C,
        condition="revaluation reported",
    ),
    _s("Guarantee", "sharing", "Gar", "Compart", "A2", C, "Anexo 49", "guarantee rules"),
    _s("AdditionalInformation", "information_type", "Inf", "Tp", "A2+A2", R, "Anexo 26"),
    *(
        _s("AdditionalInformation", f, "Inf", a, fmt, C, condition="Anexo 26 subtype")
        for f, a, fmt in (
            ("code", "Cd", "A67"),
            ("identification", "Ident", "A14"),
            ("amount", "Valor", "N19,2"),
            ("percentage", "Perc", "N5,2"),
            ("quantity", "Qtd", "I9"),
        )
    ),
    *(
        _s("SicorInformation", f, "Sicor", a, fmt, req, dom, cond)
        for f, a, fmt, req, dom, cond in (
            ("bacen_reference", "RefBacen", "A11", R, None, None),
            ("destination_order", "Ordem", "N4", R, None, None),
            ("average_total_balance", "VlrSaldoTot", "N19,2", R, None, None),
            ("average_outstanding_balance", "VlrSaldoVinc", "N19,2", R, None, None),
            ("status", "Situacao", "A2", R, "Anexo 32", None),
            ("bonus_type", "TpBonusRebate", "A2", C, "Anexo 33", "bonus/rebate"),
            ("bonus_amount", "VlrBonusRebate", "N19,2", C, None, "bonus/rebate"),
            ("bonus_payment_date", "DtBonusRebate", "AAAA-MM-DD", C, None, "bonus/rebate"),
        )
    ),
    *(
        _s("Accounting4966", f, "ContInstFinRes4966", a, fmt, C, dom, cond)
        for f, a, fmt, dom, cond in (
            ("asset_classification", "ClasAtFin", "A1", "Anexo 40", "instrument category"),
            ("stage", "EstInstFin", "A1", "Anexo 41", "complete methodology"),
            (
                "instrument_quantity",
                "QtdInst",
                "N10",
                None,
                "modality 18 outside classified portfolio",
            ),
            ("gross_carrying_amount", "VlrContBr", "N19,2", None, "applicable assets"),
            ("accumulated_loss", "VlrPerdaAcum", "N19,2", None, "recognized accumulated loss"),
            ("fair_value", "VlrJusto", "N19,2", None, "FVOCI or FVTPL"),
            ("effective_interest_rate", "TJE", "N11,7", None, "pure EIR method"),
            ("monthly_income", "RendMes", "N19,2", None, "applicable operations"),
            ("stage_one_pd_type", "PdEst1", "A1", "S/N", "Stage 1 complete methodology"),
            (
                "minimum_provision_portfolio",
                "CartProvMin",
                "A2",
                "Anexo 43",
                "minimum provision scope",
            ),
            ("isolated_credit_risk_treatment", "TratRisc", "A1", "S/N", "isolated treatment"),
        )
    ),
    _s("StageAllocation", "reason", "Estagio", "Motivo", "A3", R, "Anexo 42"),
    _s("StageAllocation", "allocation_month", "Estagio", "DtAlocacao", "AAAA-MM", R),
    _s("RecognizedLoss", "reason", "Perda", "MotPerda", "A2", R, "Anexo 44"),
    _s("RecognizedLoss", "amount", "Perda", "VlrPerda", "N19,2", R),
    _s("ConnectedIpoc", "ipoc", "ipocCon", "ipoc", "A67", R),
    *(
        _s("Aggregation", f, "Agreg", a, fmt, req, dom, cond)
        for f, a, fmt, req, dom, cond in (
            ("nature", "NatuOp", "A2", R, "Anexo 2", None),
            ("modality", "Mod", "A4", R, "Anexo 3", None),
            ("resource_origin", "OrigemRec", "A4", R, "Anexo 4 + 00", None),
            ("foreign_currency_link", "VincME", "A1", R, "Anexo 18", None),
            ("value_band", "FaixaVlr", "A1", R, "Anexo 14", None),
            ("location", "Localiz", "A5", R, "Anexo 7", None),
            ("client_type", "TpCli", "A1", R, "Anexo 11", None),
            ("control_type", "TpCtrl", "A2", C, "Anexo 10", "PJ"),
            ("performance", "DesempOp", "A2", R, "Anexo 28", None),
            (
                "special_characteristic",
                "CaracEspecial",
                "A2",
                OPTIONAL,
                "Anexo 8 priority subset",
                None,
            ),
            ("provision", "ProvConsttd", "N19,2", R, None, None),
            ("operation_count", "QtdOp", "N9", R, None, None),
            ("client_count", "QtdCli", "N9", R, None, None),
            ("maturities", "vCOD", "N19,2", R, "Anexo 1", None),
        )
    ),
)


def sourced[T](value: T, *, system: str, field: str, evidence_id: str) -> SourcedValue[T]:
    return SourcedValue(
        value=value, origin=SourceRef(system=system, field=field, evidence_id=evidence_id)
    )


def _v[T](item: SourcedValue[T]) -> T:
    return item.value


def _text(item: SourcedValue[str], name: str, maximum: int, digits: bool = False) -> str:
    value = _v(item)
    if not isinstance(value, str) or not value or value != value.strip():
        raise DomainValidationError(f"{name} must be a non-empty trimmed string")
    if len(value) > maximum or (digits and not value.isdigit()):
        raise DomainValidationError(f"{name} has an invalid format")
    return value


def _non_negative(item: SourcedValue[Decimal] | SourcedValue[int], name: str) -> Decimal:
    value = Decimal(str(_v(item)))
    if value < 0:
        raise DomainValidationError(f"{name} must be non-negative")
    return value


def _group(name: str, values: tuple[object | None, ...]) -> None:
    count = sum(value is not None for value in values)
    if count not in {0, len(values)}:
        raise DomainValidationError(f"{name} must be supplied as a complete conditional group")


@dataclass(frozen=True, slots=True, kw_only=True)
class Header:
    reference_month: SourcedValue[date]
    reporting_entity_cnpj: SourcedValue[str]
    part: SourcedValue[int]
    remittance: SourcedValue[int]
    file_type: SourcedValue[str] | None
    responsible_name: SourcedValue[str]
    responsible_email: SourcedValue[str]
    responsible_phone: SourcedValue[str]
    total_clients: SourcedValue[int]
    expected_loss_methodology: SourcedValue[str] | None
    differentiated_eir_method: SourcedValue[str] | None
    fund_type: SourcedValue[str] | None

    def __post_init__(self) -> None:
        if _v(self.reference_month).day != 1:
            raise DomainValidationError("reference_month must be the first day of its month")
        if len(_text(self.reporting_entity_cnpj, "reporting_entity_cnpj", 8, True)) != 8:
            raise DomainValidationError("reporting_entity_cnpj must have exactly 8 digits")
        if _v(self.part) < 1 or _v(self.remittance) < 1:
            raise DomainValidationError("part and remittance must be positive")
        if _v(self.total_clients) < 0:
            raise DomainValidationError("total_clients must be non-negative")
        _text(self.responsible_name, "responsible_name", 100)
        if not re.fullmatch(
            r"[^@\s]+@[^@\s]+\.[^@\s]+", _text(self.responsible_email, "responsible_email", 254)
        ):
            raise DomainValidationError("responsible_email has an invalid format")
        _text(self.responsible_phone, "responsible_phone", 20, True)
        if self.fund_type is None and (
            self.expected_loss_methodology is None or self.differentiated_eir_method is None
        ):
            raise DomainValidationError(
                "expected_loss_methodology and differentiated_eir_method "
                "are required without fund_type"
            )
        if self.fund_type is not None and (
            self.expected_loss_methodology is not None or self.differentiated_eir_method is not None
        ):
            raise DomainValidationError(
                "fund_type is exclusive with expected-loss and differentiated-EIR methods"
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class MaturityValue:
    vertex: SourcedValue[str]
    amount: SourcedValue[Decimal]

    def __post_init__(self) -> None:
        if not re.fullmatch(r"v\d{1,3}", _text(self.vertex, "maturity vertex", 4)):
            raise DomainValidationError("maturity vertex must use the vCOD form")
        _non_negative(self.amount, "maturity amount")


@dataclass(frozen=True, slots=True, kw_only=True)
class Guarantee:
    status: SourcedValue[str] | None
    guarantee_type: SourcedValue[str]
    identification: SourcedValue[str] | None
    value_type: SourcedValue[str]
    percentage: SourcedValue[Decimal] | None
    original_value: SourcedValue[Decimal] | None
    revalued_value: SourcedValue[Decimal] | None
    revalued_percentage: SourcedValue[Decimal] | None
    revaluation_date: SourcedValue[date] | None
    sharing: SourcedValue[str] | None

    def __post_init__(self) -> None:
        _text(self.guarantee_type, "guarantee_type", 4)
        _text(self.value_type, "value_type", 2)
        if self.percentage is None and self.original_value is None:
            raise DomainValidationError("guarantee requires sourced percentage or original_value")
        for name in ("percentage", "original_value", "revalued_value", "revalued_percentage"):
            item = getattr(self, name)
            if item is not None:
                value = _non_negative(item, name)
                if "percentage" in name and value > 100:
                    raise DomainValidationError(f"{name} cannot exceed 100")
        if (
            self.revaluation_date is not None
            and self.revalued_value is None
            and self.revalued_percentage is None
        ):
            raise DomainValidationError("revaluation_date requires a sourced revalued value")


@dataclass(frozen=True, slots=True, kw_only=True)
class AdditionalInformation:
    information_type: SourcedValue[str]
    code: SourcedValue[str] | None
    identification: SourcedValue[str] | None
    amount: SourcedValue[Decimal] | None
    percentage: SourcedValue[Decimal] | None
    quantity: SourcedValue[int] | None

    def __post_init__(self) -> None:
        _text(self.information_type, "information_type", 4)
        if all(
            x is None
            for x in (self.code, self.identification, self.amount, self.percentage, self.quantity)
        ):
            raise DomainValidationError("additional information requires a sourced payload")


@dataclass(frozen=True, slots=True, kw_only=True)
class SicorInformation:
    bacen_reference: SourcedValue[str]
    destination_order: SourcedValue[int]
    average_total_balance: SourcedValue[Decimal]
    average_outstanding_balance: SourcedValue[Decimal]
    status: SourcedValue[str]
    bonus_type: SourcedValue[str] | None
    bonus_amount: SourcedValue[Decimal] | None
    bonus_payment_date: SourcedValue[date] | None

    def __post_init__(self) -> None:
        _text(self.bacen_reference, "bacen_reference", 11)
        if _v(self.destination_order) < 1:
            raise DomainValidationError("destination_order must be positive")
        _non_negative(self.average_total_balance, "average_total_balance")
        _non_negative(self.average_outstanding_balance, "average_outstanding_balance")
        _group("Sicor bonus/rebate", (self.bonus_type, self.bonus_amount, self.bonus_payment_date))


@dataclass(frozen=True, slots=True, kw_only=True)
class StageAllocation:
    reason: SourcedValue[str]
    allocation_month: SourcedValue[date]

    def __post_init__(self) -> None:
        _text(self.reason, "stage allocation reason", 3)
        if _v(self.allocation_month).day != 1:
            raise DomainValidationError("allocation_month must be the first day of its month")


@dataclass(frozen=True, slots=True, kw_only=True)
class RecognizedLoss:
    reason: SourcedValue[str]
    amount: SourcedValue[Decimal]

    def __post_init__(self) -> None:
        _text(self.reason, "loss reason", 2)
        _non_negative(self.amount, "loss amount")


@dataclass(frozen=True, slots=True, kw_only=True)
class Accounting4966:
    asset_classification: SourcedValue[str] | None
    stage: SourcedValue[str] | None
    instrument_quantity: SourcedValue[int] | None
    gross_carrying_amount: SourcedValue[Decimal] | None
    accumulated_loss: SourcedValue[Decimal] | None
    fair_value: SourcedValue[Decimal] | None
    effective_interest_rate: SourcedValue[Decimal] | None
    monthly_income: SourcedValue[Decimal] | None
    stage_one_pd_type: SourcedValue[str] | None
    minimum_provision_portfolio: SourcedValue[str] | None
    isolated_credit_risk_treatment: SourcedValue[str] | None
    stage_allocations: tuple[StageAllocation, ...]
    recognized_losses: tuple[RecognizedLoss, ...]

    def __post_init__(self) -> None:
        if all(getattr(self, f.name) in (None, ()) for f in fields(self)):
            raise DomainValidationError("Accounting4966 must contain sourced information")
        for name in (
            "instrument_quantity",
            "gross_carrying_amount",
            "accumulated_loss",
            "fair_value",
        ):
            item = getattr(self, name)
            if item is not None:
                _non_negative(item, name)
        if self.accumulated_loss is not None and self.gross_carrying_amount is None:
            raise DomainValidationError("accumulated_loss requires gross_carrying_amount")
        if self.stage_allocations and self.stage is None:
            raise DomainValidationError("stage allocations require an explicit sourced stage")


@dataclass(frozen=True, slots=True, kw_only=True)
class Operation:
    detailed_client: SourcedValue[str] | None
    ipoc: SourcedValue[str]
    contract_code: SourcedValue[str]
    modality: SourcedValue[str]
    cosif_accounts: SourcedValue[str]
    resource_origin: SourcedValue[str]
    indexer: SourcedValue[str]
    indexer_percentage: SourcedValue[Decimal]
    currency_variation: SourcedValue[str]
    postal_code: SourcedValue[str]
    effective_annual_rate: SourcedValue[Decimal]
    contract_date: SourcedValue[date]
    contracted_amount: SourcedValue[Decimal] | None
    nature: SourcedValue[str]
    maturity_date: SourcedValue[date] | None
    provision: SourcedValue[Decimal]
    days_past_due: SourcedValue[int] | None
    special_characteristics: SourcedValue[str] | None
    next_installment_date: SourcedValue[date] | None
    next_installment_amount: SourcedValue[Decimal] | None
    installment_count: SourcedValue[int] | None
    maturities: tuple[MaturityValue, ...]
    guarantees: tuple[Guarantee, ...]
    additional_information: tuple[AdditionalInformation, ...]
    sicor: SicorInformation | None
    accounting_4966: Accounting4966 | None

    def __post_init__(self) -> None:
        for item, name, size in (
            (self.ipoc, "ipoc", 67),
            (self.contract_code, "contract_code", 40),
            (self.modality, "modality", 4),
            (self.cosif_accounts, "cosif_accounts", 255),
            (self.resource_origin, "resource_origin", 4),
            (self.indexer, "indexer", 2),
            (self.currency_variation, "currency_variation", 3),
            (self.nature, "nature", 2),
        ):
            _text(item, name, size)
        if len(_text(self.postal_code, "postal_code", 8, True)) != 8:
            raise DomainValidationError("postal_code must have exactly 8 digits")
        _non_negative(self.provision, "provision")
        if self.contracted_amount is not None:
            _non_negative(self.contracted_amount, "contracted_amount")
        if self.maturity_date is not None and _v(self.maturity_date) < _v(self.contract_date):
            raise TemporalConsistencyError("maturity_date cannot precede contract_date")
        _group("next installment", (self.next_installment_date, self.next_installment_amount))
        vertices = [_v(x.vertex) for x in self.maturities]
        if len(vertices) != len(set(vertices)):
            raise DomainValidationError("maturity vertices must be unique per operation")
        if any(205 <= int(v[1:]) <= 330 for v in vertices) and self.days_past_due is None:
            raise DomainValidationError(
                "days_past_due is required for maturity vertices 205 through 330"
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class Client:
    code: SourcedValue[str]
    client_type: SourcedValue[str]
    authorization: SourcedValue[str]
    client_size: SourcedValue[str]
    control_type: SourcedValue[str] | None
    relationship_start: SourcedValue[date]
    income: SourcedValue[Decimal]
    economic_group: SourcedValue[str] | None
    foreign_name: SourcedValue[str] | None
    foreign_id_type: SourcedValue[str] | None
    foreign_id: SourcedValue[str] | None
    leader_cnpj: SourcedValue[str] | None
    country_code: SourcedValue[str] | None
    operations: tuple[Operation, ...]

    def __post_init__(self) -> None:
        _text(self.code, "client code", 14)
        kind = _text(self.client_type, "client_type", 1)
        _text(self.client_size, "client_size", 1)
        _non_negative(self.income, "income")
        if kind == "2" and self.control_type is None:
            raise DomainValidationError("control_type is required for PJ clients")
        _group(
            "foreign client identification",
            (self.foreign_name, self.foreign_id_type, self.foreign_id, self.country_code),
        )
        if not self.operations:
            raise DomainValidationError("an individualized client requires at least one operation")
        if kind == "2" and any(op.detailed_client is None for op in self.operations):
            raise DomainValidationError("detailed_client is required for PJ operations")


@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectedIpoc:
    ipoc: SourcedValue[str]

    def __post_init__(self) -> None:
        _text(self.ipoc, "connected ipoc", 67)


@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectedIpocGroup:
    ipocs: tuple[ConnectedIpoc, ...]

    def __post_init__(self) -> None:
        values = [_v(x.ipoc) for x in self.ipocs]
        if len(values) < 2 or len(values) != len(set(values)):
            raise DomainValidationError("connected IPOC group requires at least two unique IPOCs")


@dataclass(frozen=True, slots=True, kw_only=True)
class Aggregation:
    nature: SourcedValue[str]
    modality: SourcedValue[str]
    resource_origin: SourcedValue[str]
    foreign_currency_link: SourcedValue[str]
    value_band: SourcedValue[str]
    location: SourcedValue[str]
    client_type: SourcedValue[str]
    control_type: SourcedValue[str] | None
    performance: SourcedValue[str]
    special_characteristic: SourcedValue[str] | None
    provision: SourcedValue[Decimal]
    operation_count: SourcedValue[int]
    client_count: SourcedValue[int]
    maturities: tuple[MaturityValue, ...]

    def __post_init__(self) -> None:
        if _v(self.client_type) == "2" and self.control_type is None:
            raise DomainValidationError("control_type is required for PJ aggregations")
        _non_negative(self.provision, "aggregation provision")
        if _v(self.operation_count) < 1 or _v(self.client_count) < 1:
            raise DomainValidationError("aggregation counts must be positive")
        if not self.maturities:
            raise DomainValidationError("aggregation requires sourced maturity values")


@dataclass(frozen=True, slots=True, kw_only=True)
class Doc3040Input:
    header: Header
    clients: tuple[Client, ...]
    aggregations: tuple[Aggregation, ...]
    connected_ipoc_groups: tuple[ConnectedIpocGroup, ...]

    def __post_init__(self) -> None:
        if not self.clients and not self.aggregations:
            raise DomainValidationError("Doc3040 requires individualized clients or aggregations")
        codes = [_v(x.code) for x in self.clients]
        if len(codes) != len(set(codes)):
            raise DomainValidationError("client codes must be unique")
        if _v(self.header.total_clients) != len(set(codes)):
            raise DomainValidationError(
                "total_clients must reconcile to distinct individualized clients"
            )
        ipocs = [_v(op.ipoc) for client in self.clients for op in client.operations]
        if len(ipocs) != len(set(ipocs)):
            raise DomainValidationError("operation IPOCs must be unique")
        for group in self.connected_ipoc_groups:
            if set(_v(x.ipoc) for x in group.ipocs) - set(ipocs):
                raise DomainValidationError("connected IPOCs must exist in document operations")
        month = _v(self.header.reference_month)
        if any(_v(c.relationship_start) >= month for c in self.clients):
            raise TemporalConsistencyError("relationship_start must precede reference_month")


def catalog_fields_for(model: type[object]) -> tuple[FieldSpec, ...]:
    return tuple(spec for spec in FIELD_CATALOG if spec.model == model.__name__)


def assert_catalog_covers_models() -> None:
    structural = {
        "operations",
        "maturities",
        "guarantees",
        "additional_information",
        "sicor",
        "accounting_4966",
        "stage_allocations",
        "recognized_losses",
        "ipocs",
    }
    models = (
        Header,
        Client,
        Operation,
        MaturityValue,
        Guarantee,
        AdditionalInformation,
        SicorInformation,
        Accounting4966,
        StageAllocation,
        RecognizedLoss,
        ConnectedIpoc,
        Aggregation,
    )
    catalog = {(x.model, x.field) for x in FIELD_CATALOG}
    missing = {
        (model.__name__, f.name)
        for model in models
        for f in fields(model)
        if f.name not in structural and (model.__name__, f.name) not in catalog
    }
    if missing:
        raise AssertionError(f"Doc3040 field catalog is incomplete: {sorted(missing)}")


def iter_sourced_values(
    value: object, path: str = ""
) -> tuple[tuple[str, SourcedValue[object]], ...]:
    result: list[tuple[str, SourcedValue[object]]] = []
    if isinstance(value, SourcedValue):
        result.append((path, value))
    elif is_dataclass(value):
        for item in fields(value):
            child = getattr(value, item.name)
            child_path = f"{path}.{item.name}" if path else item.name
            result.extend(iter_sourced_values(child, child_path))
    elif isinstance(value, tuple):
        for index, child in enumerate(value):
            result.extend(iter_sourced_values(child, f"{path}[{index}]"))
    return tuple(result)
