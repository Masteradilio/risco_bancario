import csv
from pathlib import Path

MATRIX = Path("docs/regulatory/TRACEABILITY_MATRIX.csv")
REGISTER = Path("docs/regulatory/SOURCE_REGISTER.md")
REQUIRED_TOPICS = {
    "impairment",
    "ecl",
    "sicr",
    "default",
    "cure",
    "write-off",
    "forward-looking",
    "discounting",
    "poci",
    "disclosure",
    "doc3040",
}


def rows() -> list[dict[str, str]]:
    with MATRIX.open(encoding="utf-8", newline="") as source:
        return list(csv.DictReader(source))


def test_matrix_has_unique_requirements_and_required_topics() -> None:
    matrix = rows()
    identifiers = [row["requirement_id"] for row in matrix]
    assert len(identifiers) == len(set(identifiers))
    assert REQUIRED_TOPICS <= {row["topic"] for row in matrix}


def test_every_source_is_registered() -> None:
    register = REGISTER.read_text(encoding="utf-8")
    assert all(row["source_id"] in register for row in rows())


def test_implemented_requirements_have_code_test_and_evidence() -> None:
    implemented = [row for row in rows() if row["implementation_status"] == "implemented"]
    for row in implemented:
        assert row["code"] and row["test"] and row["evidence"]
        assert all(Path(path.strip()).exists() for path in row["test"].split(";"))


def test_partial_requirements_point_to_existing_evidence_surfaces() -> None:
    partial = [row for row in rows() if row["implementation_status"] == "partial"]
    assert partial
    for row in partial:
        assert all(Path(path.strip()).exists() for path in row["test"].split(";"))
        assert row["evidence"].startswith("partial:")


def test_not_applicable_requirements_have_reason_and_evidence() -> None:
    not_applicable = [row for row in rows() if row["applicability"] == "not_applicable"]
    assert not_applicable
    for row in not_applicable:
        assert row["implementation_status"] == "not_applicable"
        assert len(row["applicability_rationale"]) >= 20
        assert row["evidence"]
