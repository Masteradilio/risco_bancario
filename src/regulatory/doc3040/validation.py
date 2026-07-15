"""Layered local pre-validation for generated Document 3040 XML candidates."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from pathlib import Path

from lxml import etree  # type: ignore[import-untyped]

from ...domain.exceptions import DomainValidationError
from .layout_registry import LayoutVersion, layout_for_reference_month, load_derived_xsd

DEFAULT_DOMAIN_FILE = Path("config/regulatory/doc3040/domains/2026.07-supported-subset.json")


class IssueSeverity(StrEnum):
    WARNING = "warning"
    ERROR = "error"
    BLOCKER = "blocker"


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    rule_id: str
    severity: IssueSeverity
    message: str
    line: int | None
    field: str | None
    path: str


@dataclass(frozen=True, slots=True)
class PortfolioEclControl:
    ipoc: str
    gross_carrying_amount: Decimal
    ecl_amount: Decimal
    evidence_id: str

    def __post_init__(self) -> None:
        if not self.ipoc or not self.evidence_id:
            raise DomainValidationError("portfolio control requires IPOC and evidence_id")
        if self.gross_carrying_amount < 0 or self.ecl_amount < 0:
            raise DomainValidationError("portfolio control amounts must be non-negative")


@dataclass(frozen=True, slots=True)
class PrevalidationReport:
    layout_version: str
    domain_set_id: str
    passed: bool
    status: str
    derived_xsd_passed: bool
    official_xsd_executed: bool
    official_critics_executed: bool
    issues: tuple[ValidationIssue, ...]

    @property
    def errors(self) -> tuple[ValidationIssue, ...]:
        return tuple(
            issue
            for issue in self.issues
            if issue.severity in {IssueSeverity.ERROR, IssueSeverity.BLOCKER}
        )


def _issue(
    rule_id: str,
    severity: IssueSeverity,
    message: str,
    element: etree._Element | None,
    field: str | None = None,
) -> ValidationIssue:
    return ValidationIssue(
        rule_id,
        severity,
        message,
        element.sourceline if element is not None else None,
        field,
        element.getroottree().getpath(element) if element is not None else "/",
    )


def _parse_month(root: etree._Element) -> date:
    raw = root.get("DtBase")
    try:
        return date.fromisoformat(f"{raw}-01")
    except (TypeError, ValueError) as exc:
        raise DomainValidationError("Doc3040 DtBase must use YYYY-MM") from exc


def _load_domains(layout: LayoutVersion, path: Path) -> tuple[str, Mapping[str, frozenset[str]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("layout_version") != layout.version:
        raise DomainValidationError("domain set does not match selected layout version")
    source_hash = layout.artifact("layout_and_domains").sha256
    if payload.get("derived_from_layout_sha256") != source_hash:
        raise DomainValidationError("domain set is not bound to the selected official layout hash")
    raw_values = payload.get("values")
    if not isinstance(raw_values, dict):
        raise DomainValidationError("domain set values must be an object")
    values: dict[str, frozenset[str]] = {}
    for name, raw in raw_values.items():
        if not isinstance(raw, list) or not raw or not all(isinstance(item, str) for item in raw):
            raise DomainValidationError(f"domain {name} must be a non-empty string list")
        values[name] = frozenset(raw)
    return str(payload["domain_set_id"]), values


def _check_domain(
    issues: list[ValidationIssue],
    element: etree._Element,
    attribute: str,
    domain_name: str,
    domains: Mapping[str, frozenset[str]],
    *,
    required: bool = False,
) -> None:
    value = element.get(attribute)
    if value is None:
        if required:
            issues.append(
                _issue(
                    "LOCAL-REQUIRED",
                    IssueSeverity.ERROR,
                    f"required attribute {attribute} is absent",
                    element,
                    attribute,
                )
            )
        return
    if value not in domains[domain_name]:
        issues.append(
            _issue(
                "LOCAL-DOMAIN",
                IssueSeverity.ERROR,
                f"{attribute}={value!r} is outside versioned domain {domain_name}",
                element,
                attribute,
            )
        )


def _validate_domains(
    root: etree._Element, domains: Mapping[str, frozenset[str]]
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for attribute, domain, required in (
        ("TpArq", "file_type", False),
        ("MetodApPE", "expected_loss_methodology", False),
        ("MetodDifTJE", "yes_no", False),
    ):
        _check_domain(issues, root, attribute, domain, domains, required=required)
    for client in root.findall("Cli"):
        _check_domain(issues, client, "Tp", "client_type", domains, required=True)
        _check_domain(issues, client, "Autorzc", "authorization", domains, required=True)
        size_domain = "pj_size" if client.get("Tp") == "2" else "pf_size"
        _check_domain(issues, client, "PorteCli", size_domain, domains, required=True)
        _check_domain(issues, client, "TpCtrl", "control_type", domains)
        for operation in client.findall("Op"):
            for attribute, domain in (
                ("Mod", "modality_supported"),
                ("OrigemRec", "resource_origin_supported"),
                ("Indx", "indexer"),
                ("VarCamb", "currency_variation"),
                ("NatuOp", "nature"),
            ):
                _check_domain(issues, operation, attribute, domain, domains, required=True)
            for maturity in operation.findall("Venc"):
                for vertex in maturity.attrib:
                    if vertex not in domains["maturity_vertex"]:
                        issues.append(
                            _issue(
                                "LOCAL-DOMAIN",
                                IssueSeverity.ERROR,
                                f"unsupported maturity vertex {vertex}",
                                maturity,
                                vertex,
                            )
                        )
            for guarantee in operation.findall("Gar"):
                for attribute, domain in (
                    ("Tp", "guarantee_type_supported"),
                    ("SitGar", "guarantee_status"),
                    ("TpVlrGar", "guarantee_value_type"),
                    ("Compart", "guarantee_sharing"),
                ):
                    _check_domain(issues, guarantee, attribute, domain, domains)
            for information in operation.findall("Inf"):
                _check_domain(
                    issues,
                    information,
                    "Tp",
                    "additional_information_supported",
                    domains,
                    required=True,
                )
            sicor = operation.find("Sicor")
            if sicor is not None:
                _check_domain(issues, sicor, "Situacao", "sicor_status", domains, required=True)
            accounting = operation.find("ContInstFinRes4966")
            if accounting is not None:
                for attribute, domain in (
                    ("ClasAtFin", "asset_classification"),
                    ("EstInstFin", "stage"),
                    ("PdEst1", "yes_no"),
                    ("CartProvMin", "minimum_provision_portfolio"),
                    ("TratRisc", "yes_no"),
                ):
                    _check_domain(issues, accounting, attribute, domain, domains)
                for stage in accounting.findall("Estagio"):
                    _check_domain(issues, stage, "Motivo", "stage_reason", domains, required=True)
                for loss in accounting.findall("Perda"):
                    _check_domain(issues, loss, "MotPerda", "loss_reason", domains, required=True)
    for aggregate in root.findall("Agreg"):
        for attribute, domain in (
            ("NatuOp", "nature"),
            ("Mod", "modality_supported"),
            ("OrigemRec", "resource_origin_supported"),
            ("VincME", "yes_no"),
            ("FaixaVlr", "value_band"),
            ("TpCli", "client_type"),
            ("TpCtrl", "control_type"),
        ):
            _check_domain(issues, aggregate, attribute, domain, domains)
    return issues


def _decimal(element: etree._Element, attribute: str) -> Decimal | None:
    raw = element.get(attribute)
    if raw is None:
        return None
    try:
        return Decimal(raw)
    except InvalidOperation:
        return None


def _reported_ipoc(root: etree._Element, client: etree._Element, operation: etree._Element) -> str:
    client_type = client.get("Tp", "")
    client_code = client.get("Cd", "")
    component = (
        client_code
        if client_type == "1"
        else client_code[:8] if client_type == "2" else client_code.zfill(14)
    )
    return "".join(
        (
            root.get("CNPJ", ""),
            operation.get("Mod", ""),
            client_type,
            component,
            operation.get("Contrt", ""),
        )
    )


def _validate_semantics(
    root: etree._Element, controls: tuple[PortfolioEclControl, ...]
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    clients = root.findall("Cli")
    aggregates = root.findall("Agreg")
    if not aggregates and root.get("TotalCli") != str(
        len({client.get("Cd") for client in clients})
    ):
        issues.append(
            _issue(
                "LOCAL-TOTAL-CLIENTS",
                IssueSeverity.ERROR,
                "TotalCli does not reconcile to distinct individualized clients",
                root,
                "TotalCli",
            )
        )
    control_map = {control.ipoc: control for control in controls}
    if len(control_map) != len(controls):
        raise DomainValidationError("portfolio controls must have unique IPOCs")
    seen_ipocs: set[str] = set()
    for client in clients:
        seen_contracts: set[tuple[str | None, str | None]] = set()
        for operation in client.findall("Op"):
            ipoc = operation.get("IPOC", "")
            if ipoc in seen_ipocs:
                issues.append(
                    _issue(
                        "LOCAL-IPOC-UNIQUE",
                        IssueSeverity.ERROR,
                        "duplicate IPOC",
                        operation,
                        "IPOC",
                    )
                )
            seen_ipocs.add(ipoc)
            contract_key = (operation.get("Mod"), operation.get("Contrt"))
            if contract_key in seen_contracts:
                issues.append(
                    _issue(
                        "LOCAL-CONTRACT-UNIQUE",
                        IssueSeverity.ERROR,
                        "duplicate contract for client and modality",
                        operation,
                        "Contrt",
                    )
                )
            seen_contracts.add(contract_key)
            expected_ipoc = _reported_ipoc(root, client, operation)
            if ipoc != expected_ipoc:
                issues.append(
                    _issue(
                        "LOCAL-IPOC-COMPONENTS",
                        IssueSeverity.ERROR,
                        f"IPOC components imply {expected_ipoc}",
                        operation,
                        "IPOC",
                    )
                )
            control = control_map.get(ipoc)
            if control is None:
                issues.append(
                    _issue(
                        "LOCAL-PORTFOLIO-CONTROL",
                        IssueSeverity.BLOCKER,
                        "missing portfolio/ECL control",
                        operation,
                        "IPOC",
                    )
                )
                continue
            accounting = operation.find("ContInstFinRes4966")
            if accounting is None:
                issues.append(
                    _issue(
                        "LOCAL-ECL-BLOCK",
                        IssueSeverity.ERROR,
                        "missing ContInstFinRes4966 for portfolio reconciliation",
                        operation,
                        "ContInstFinRes4966",
                    )
                )
                continue
            gross = _decimal(accounting, "VlrContBr")
            loss = _decimal(accounting, "VlrPerdaAcum")
            if gross != control.gross_carrying_amount:
                issues.append(
                    _issue(
                        "LOCAL-PORTFOLIO-GROSS",
                        IssueSeverity.ERROR,
                        f"VlrContBr does not reconcile to control {control.evidence_id}",
                        accounting,
                        "VlrContBr",
                    )
                )
            if loss != control.ecl_amount:
                issues.append(
                    _issue(
                        "LOCAL-PORTFOLIO-ECL",
                        IssueSeverity.ERROR,
                        f"VlrPerdaAcum does not reconcile to control {control.evidence_id}",
                        accounting,
                        "VlrPerdaAcum",
                    )
                )
            if gross is not None and loss is not None and loss > gross:
                issues.append(
                    _issue(
                        "LOCAL-ECL-BOUND",
                        IssueSeverity.ERROR,
                        "accumulated loss exceeds gross carrying amount",
                        accounting,
                        "VlrPerdaAcum",
                    )
                )
            maturity_total = sum(
                (
                    Decimal(raw)
                    for maturity in operation.findall("Venc")
                    for raw in maturity.attrib.values()
                ),
                Decimal("0"),
            )
            if gross is not None and maturity_total != gross:
                issues.append(
                    _issue(
                        "LOCAL-MATURITY-TOTAL",
                        IssueSeverity.ERROR,
                        "maturity vertices do not reconcile to gross carrying amount "
                        "in the supported perimeter",
                        operation.find("Venc"),
                        "Venc",
                    )
                )
    unexpected_controls = set(control_map) - seen_ipocs
    for ipoc in sorted(unexpected_controls):
        issues.append(
            _issue(
                "LOCAL-CONTROL-ORPHAN",
                IssueSeverity.ERROR,
                f"portfolio control {ipoc} has no XML operation",
                root,
                "IPOC",
            )
        )
    issues.append(
        _issue(
            "BCB-CRITICS-NOT-EXECUTED",
            IssueSeverity.WARNING,
            "official BCB critic workbook is versioned but this run executes only "
            "the local supported semantic subset",
            root,
        )
    )
    return issues


def prevalidate_xml(
    content: bytes,
    controls: tuple[PortfolioEclControl, ...],
    *,
    domain_path: Path = DEFAULT_DOMAIN_FILE,
) -> PrevalidationReport:
    parser = etree.XMLParser(resolve_entities=False, no_network=True, remove_blank_text=False)
    try:
        root = etree.fromstring(content, parser)
    except etree.XMLSyntaxError as exc:
        issue = ValidationIssue("XML-PARSE", IssueSeverity.BLOCKER, str(exc), exc.lineno, None, "/")
        return PrevalidationReport(
            "unresolved", "unresolved", False, "REJECTED", False, False, False, (issue,)
        )
    try:
        layout = layout_for_reference_month(_parse_month(root))
        domain_set_id, domains = _load_domains(layout, domain_path)
    except DomainValidationError as exc:
        issue = _issue("LAYOUT-RESOLUTION", IssueSeverity.BLOCKER, str(exc), root, "DtBase")
        return PrevalidationReport(
            "unresolved", "unresolved", False, "REJECTED", False, False, False, (issue,)
        )
    issues: list[ValidationIssue] = []
    schema = etree.XMLSchema(etree.fromstring(load_derived_xsd(layout)))
    derived_xsd_passed = schema.validate(root)
    if not derived_xsd_passed:
        for error in schema.error_log:
            issues.append(
                ValidationIssue(
                    "DERIVED-XSD", IssueSeverity.ERROR, error.message, error.line, None, "/"
                )
            )
    issues.extend(_validate_domains(root, domains))
    issues.extend(_validate_semantics(root, controls))
    issues.append(
        _issue(
            "OFFICIAL-XSD-NOT-AVAILABLE",
            IssueSeverity.WARNING,
            layout.xsd_status,
            root,
        )
    )
    passed = not any(
        issue.severity in {IssueSeverity.ERROR, IssueSeverity.BLOCKER} for issue in issues
    )
    return PrevalidationReport(
        layout.version,
        domain_set_id,
        passed,
        "PREVALIDATED_DERIVED_XSD" if passed else "REJECTED",
        derived_xsd_passed,
        False,
        False,
        tuple(issues),
    )
