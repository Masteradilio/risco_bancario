import copy
import json
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest
from lxml import etree

from src.domain.exceptions import DomainValidationError
from src.regulatory.doc3040 import (
    Accounting4966,
    IssueSeverity,
    PortfolioEclControl,
    generate_xml_candidate,
    load_layout_registry,
    prevalidate_xml,
)
from src.regulatory.doc3040.validation import _load_domains
from tests.regulatory.test_doc3040_generator import base_document, base_operation, sv


def reconciled_document(*, gross: Decimal = Decimal("980"), loss: Decimal = Decimal("20")):
    accounting = Accounting4966(
        asset_classification=sv("1", "asset_classification"),
        stage=sv("1", "stage"),
        instrument_quantity=None,
        gross_carrying_amount=sv(gross, "gross_carrying_amount"),
        accumulated_loss=sv(loss, "accumulated_loss"),
        fair_value=None,
        effective_interest_rate=sv(Decimal("12.5"), "eir"),
        monthly_income=sv(Decimal("10"), "monthly_income"),
        stage_one_pd_type=sv("N", "stage_one_pd_type"),
        minimum_provision_portfolio=sv("C1", "minimum_portfolio"),
        isolated_credit_risk_treatment=sv("N", "isolated_treatment"),
        stage_allocations=(),
        recognized_losses=(),
    )
    return base_document(replace(base_operation(), accounting_4966=accounting))


def controls(*, gross: Decimal = Decimal("980"), loss: Decimal = Decimal("20")):
    return (
        PortfolioEclControl(
            ipoc="123456780203112345678901CONTRATO1",
            gross_carrying_amount=gross,
            ecl_amount=loss,
            evidence_id="ECL-LEDGER-2026-07",
        ),
    )


def test_doc3040_crit_001_passes_layered_local_prevalidation_with_explicit_limits() -> None:
    candidate = generate_xml_candidate(reconciled_document())
    report = prevalidate_xml(candidate.content, controls())
    assert report.passed
    assert report.status == "PREVALIDATED_DERIVED_XSD"
    assert report.derived_xsd_passed
    assert not report.official_xsd_executed
    assert not report.official_critics_executed
    assert not report.errors
    assert {issue.rule_id for issue in report.issues} == {
        "BCB-CRITICS-NOT-EXECUTED",
        "OFFICIAL-XSD-NOT-AVAILABLE",
    }
    assert all(issue.severity == IssueSeverity.WARNING for issue in report.issues)


def test_derived_xsd_reports_line_and_missing_field() -> None:
    content = generate_xml_candidate(reconciled_document()).content.replace(b' CEP="01310100"', b"")
    report = prevalidate_xml(content, controls())
    issue = next(issue for issue in report.issues if issue.rule_id == "DERIVED-XSD")
    assert not report.passed and not report.derived_xsd_passed
    assert issue.line is not None and issue.path == "/"
    assert "CEP" in issue.message


def test_domain_error_identifies_field_path_and_rule() -> None:
    operation = replace(
        reconciled_document().clients[0].operations[0],
        modality=sv("9999", "modality"),
        ipoc=sv("123456789999112345678901CONTRATO1", "ipoc"),
    )
    report = prevalidate_xml(generate_xml_candidate(base_document(operation)).content, controls())
    issue = next(issue for issue in report.errors if issue.field == "Mod")
    assert issue.rule_id == "LOCAL-DOMAIN"
    assert issue.line is not None
    assert issue.path.endswith("/Op")


def test_totals_and_portfolio_ecl_reconciliation_reject_inconsistency() -> None:
    content = generate_xml_candidate(reconciled_document()).content
    wrong_total = content.replace(b'TotalCli="1"', b'TotalCli="2"')
    total_report = prevalidate_xml(wrong_total, controls())
    assert "LOCAL-TOTAL-CLIENTS" in {issue.rule_id for issue in total_report.errors}
    wrong_control = controls(gross=Decimal("979"), loss=Decimal("19"))
    control_report = prevalidate_xml(content, wrong_control)
    assert {"LOCAL-PORTFOLIO-GROSS", "LOCAL-PORTFOLIO-ECL"} <= {
        issue.rule_id for issue in control_report.errors
    }


def test_maturity_and_ecl_bounds_are_semantically_checked() -> None:
    document = reconciled_document(gross=Decimal("900"), loss=Decimal("901"))
    report = prevalidate_xml(
        generate_xml_candidate(document).content,
        controls(gross=Decimal("900"), loss=Decimal("901")),
    )
    assert {"LOCAL-ECL-BOUND", "LOCAL-MATURITY-TOTAL"} <= {issue.rule_id for issue in report.errors}


def test_missing_and_orphan_portfolio_controls_are_reported() -> None:
    content = generate_xml_candidate(reconciled_document()).content
    missing = prevalidate_xml(content, ())
    assert (
        next(
            issue for issue in missing.errors if issue.rule_id == "LOCAL-PORTFOLIO-CONTROL"
        ).severity
        == IssueSeverity.BLOCKER
    )
    orphan = PortfolioEclControl("ORPHAN", Decimal("1"), Decimal("0"), "EV-ORPHAN")
    report = prevalidate_xml(content, (*controls(), orphan))
    assert "LOCAL-CONTROL-ORPHAN" in {issue.rule_id for issue in report.errors}


def test_malformed_xml_and_invalid_control_fail_closed() -> None:
    report = prevalidate_xml(b"<Doc3040>", ())
    assert report.status == "REJECTED"
    assert report.errors[0].rule_id == "XML-PARSE"
    with pytest.raises(DomainValidationError, match="non-negative"):
        PortfolioEclControl("IPOC", Decimal("-1"), Decimal("0"), "EV")
    with pytest.raises(DomainValidationError, match="requires IPOC"):
        PortfolioEclControl("", Decimal("1"), Decimal("0"), "EV")
    with pytest.raises(DomainValidationError, match="requires IPOC"):
        PortfolioEclControl("IPOC", Decimal("1"), Decimal("0"), "")


def test_layout_resolution_rejects_invalid_and_unsupported_months() -> None:
    content = generate_xml_candidate(reconciled_document()).content
    invalid = content.replace(b'DtBase="2026-07"', b'DtBase="invalid"')
    report = prevalidate_xml(invalid, controls())
    assert report.errors[0].rule_id == "LAYOUT-RESOLUTION"
    assert "YYYY-MM" in report.errors[0].message
    unsupported = content.replace(b'DtBase="2026-07"', b'DtBase="2024-01"')
    report = prevalidate_xml(unsupported, controls())
    assert report.errors[0].rule_id == "LAYOUT-RESOLUTION"
    assert "unsupported" in report.errors[0].message


def test_domain_file_binding_and_shape_fail_closed(tmp_path: Path) -> None:
    layout = load_layout_registry()[0]
    source = Path("config/regulatory/doc3040/domains/2026.07-supported-subset.json")
    original = json.loads(source.read_text(encoding="utf-8"))

    def reject(name: str, payload: dict, message: str) -> None:
        path = tmp_path / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        with pytest.raises(DomainValidationError, match=message):
            _load_domains(layout, path)

    wrong_layout = copy.deepcopy(original)
    wrong_layout["layout_version"] = "wrong"
    reject("layout.json", wrong_layout, "does not match")
    wrong_hash = copy.deepcopy(original)
    wrong_hash["derived_from_layout_sha256"] = "0" * 64
    reject("hash.json", wrong_hash, "not bound")
    wrong_values = copy.deepcopy(original)
    wrong_values["values"] = []
    reject("values.json", wrong_values, "must be an object")
    for index, value in enumerate(([], [1])):
        wrong_domain = copy.deepcopy(original)
        wrong_domain["values"]["client_type"] = value
        reject(f"domain-{index}.json", wrong_domain, "non-empty string list")


def test_local_domain_validator_traverses_every_supported_block() -> None:
    root = etree.fromstring(generate_xml_candidate(reconciled_document()).content)
    root.set("TpArq", "INVALID")
    client = root.find("Cli")
    assert client is not None
    client.attrib.pop("Tp")
    client.set("PorteCli", "INVALID")
    client.set("TpCtrl", "INVALID")
    operation = client.find("Op")
    assert operation is not None
    operation.set("OrigemRec", "INVALID")
    maturity = operation.find("Venc")
    assert maturity is not None
    amount = maturity.attrib.pop("v110")
    maturity.set("v999", amount)
    etree.SubElement(
        operation,
        "Gar",
        Tp="INVALID",
        SitGar="INVALID",
        TpVlrGar="INVALID",
        Compart="INVALID",
    )
    etree.SubElement(operation, "Inf", Tp="INVALID")
    etree.SubElement(operation, "Sicor", Situacao="INVALID")
    accounting = operation.find("ContInstFinRes4966")
    assert accounting is not None
    accounting.set("ClasAtFin", "INVALID")
    accounting.set("EstInstFin", "INVALID")
    etree.SubElement(accounting, "Estagio", Motivo="INVALID", DtAlocacao="2026-07")
    etree.SubElement(accounting, "Perda", MotPerda="INVALID", VlrPerda="1.00")
    etree.SubElement(
        root,
        "Agreg",
        NatuOp="INVALID",
        Mod="INVALID",
        OrigemRec="INVALID",
        VincME="INVALID",
        FaixaVlr="INVALID",
        TpCli="INVALID",
        TpCtrl="INVALID",
    )
    report = prevalidate_xml(etree.tostring(root), controls())
    local = [issue for issue in report.errors if issue.rule_id.startswith("LOCAL-")]
    assert any(issue.rule_id == "LOCAL-REQUIRED" and issue.field == "Tp" for issue in local)
    assert {issue.field for issue in local} >= {
        "TpArq",
        "PorteCli",
        "TpCtrl",
        "OrigemRec",
        "v999",
        "Tp",
        "Situacao",
        "ClasAtFin",
        "Motivo",
        "MotPerda",
    }


def test_semantic_duplicate_and_component_controls_fail_closed() -> None:
    root = etree.fromstring(generate_xml_candidate(reconciled_document()).content)
    client = root.find("Cli")
    operation = root.find("./Cli/Op")
    assert client is not None and operation is not None
    client.append(copy.deepcopy(operation))
    report = prevalidate_xml(etree.tostring(root), controls())
    assert {"LOCAL-IPOC-UNIQUE", "LOCAL-CONTRACT-UNIQUE"} <= {
        issue.rule_id for issue in report.errors
    }

    root = etree.fromstring(generate_xml_candidate(reconciled_document()).content)
    operation = root.find("./Cli/Op")
    assert operation is not None
    operation.set("IPOC", "WRONG")
    report = prevalidate_xml(etree.tostring(root), ())
    assert "LOCAL-IPOC-COMPONENTS" in {issue.rule_id for issue in report.errors}

    with pytest.raises(DomainValidationError, match="unique IPOCs"):
        prevalidate_xml(
            generate_xml_candidate(reconciled_document()).content,
            (controls()[0], controls()[0]),
        )


def test_missing_accounting_and_invalid_decimals_are_reported() -> None:
    root = etree.fromstring(generate_xml_candidate(reconciled_document()).content)
    operation = root.find("./Cli/Op")
    assert operation is not None
    accounting = operation.find("ContInstFinRes4966")
    assert accounting is not None
    operation.remove(accounting)
    report = prevalidate_xml(etree.tostring(root), controls())
    assert "LOCAL-ECL-BLOCK" in {issue.rule_id for issue in report.errors}

    root = etree.fromstring(generate_xml_candidate(reconciled_document()).content)
    accounting = root.find("./Cli/Op/ContInstFinRes4966")
    assert accounting is not None
    accounting.attrib.pop("VlrContBr")
    accounting.set("VlrPerdaAcum", "not-a-decimal")
    report = prevalidate_xml(etree.tostring(root), controls())
    assert {"LOCAL-PORTFOLIO-GROSS", "LOCAL-PORTFOLIO-ECL"} <= {
        issue.rule_id for issue in report.errors
    }
