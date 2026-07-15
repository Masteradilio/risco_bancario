"""Deterministic assistant that can only answer from persisted evidence."""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from typing import Any

from ..infrastructure.database import DatabaseManager
from ..infrastructure.database.repository import canonical_json
from .models import AgentCitation, AgentQuery, AgentResponse


class ExecutionNotFoundError(LookupError):
    """Raised when the explicitly requested execution does not exist."""


_INJECTION_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"ignore (all |any )?(previous|prior|system) instructions?",
        r"ignore (todas? |quaisquer )?(as )?(instruções|regras) anteriores",
        r"(desconsidere|esqueça).*(instruções|regras|contexto|guardrails?)",
        r"reveal (the )?(system prompt|secret|token|password)",
        r"(revele|mostre|exponha).*(prompt do sistema|segredo|token|senha)",
        r"bypass (authorization|rbac|security|guardrail)",
        r"(burle|contorne|desative).*(autorização|rbac|segurança|guardrail)",
        r"execute (sql|shell|command)",
        r"(execute|rode).*(sql|shell|comando)",
        r"(jailbreak|developer mode|modo desenvolvedor)",
    )
)


def _has_injection(question: str) -> bool:
    return any(pattern.search(question) for pattern in _INJECTION_PATTERNS)


def _hash_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class GroundedEvidenceAgent:
    """Produce bounded summaries without an LLM, web access or arbitrary tools."""

    def __init__(self, database: DatabaseManager, repository_root: Path | None = None) -> None:
        self.database = database
        self.repository_root = repository_root or Path(__file__).resolve().parents[2]

    def _execution(self, execution_id: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        execution = self.database.fetch_one(
            "SELECT execution_id, execution_key, revision, reference_date, lineage_json, "
            "lineage_hash, status, created_at FROM calculation_executions WHERE execution_id = ?",
            (execution_id,),
        )
        if execution is None:
            raise ExecutionNotFoundError(execution_id)
        results = self.database.fetch_all(
            "SELECT contract_id, period, scenario_id, ecl_amount, payload_json, payload_hash "
            "FROM calculation_results WHERE execution_id = ? "
            "ORDER BY contract_id, scenario_id, period",
            (execution_id,),
        )
        execution["lineage"] = json.loads(execution.pop("lineage_json"))
        for result in results:
            result["payload"] = json.loads(result.pop("payload_json"))
        return execution, results

    @staticmethod
    def _lineage_citation(execution: dict[str, Any]) -> AgentCitation:
        return AgentCitation(
            citation_id=f"execution:{execution['execution_id']}#lineage",
            source_type="execution_lineage",
            locator=f"calculation_executions/{execution['execution_id']}",
            source_hash=execution["lineage_hash"],
        )

    @staticmethod
    def _result_citation(execution_id: str, results: list[dict[str, Any]]) -> AgentCitation:
        hashes = [result["payload_hash"] for result in results]
        collection_hash = _hash_text(canonical_json({"result_hashes": hashes}))
        return AgentCitation(
            citation_id=f"execution:{execution_id}#results",
            source_type="execution_result",
            locator=f"calculation_results?execution_id={execution_id}",
            source_hash=collection_hash,
        )

    def _limitation(self) -> tuple[str, AgentCitation]:
        relative = Path("docs/validation/LIMITATION_REGISTER.md")
        content = (self.repository_root / relative).read_text(encoding="utf-8")
        source_hash = _hash_text(content)
        return content, AgentCitation(
            citation_id="document:limitation-register",
            source_type="document",
            locator=relative.as_posix(),
            source_hash=source_hash,
        )

    @staticmethod
    def _summary(execution: dict[str, Any], results: list[dict[str, Any]]) -> str:
        first = results[0]
        assessment = first["payload"]["stage_assessment"]
        scenario_ecl: dict[str, Decimal] = defaultdict(Decimal)
        scenario_weight: dict[str, Decimal] = {}
        for result in results:
            scenario = result["scenario_id"]
            scenario_ecl[scenario] += Decimal(str(result["ecl_amount"]))
            scenario_weight[scenario] = Decimal(str(result["payload"]["scenario_weight"]))
        weighted = sum(
            (amount * scenario_weight[scenario] for scenario, amount in scenario_ecl.items()),
            start=Decimal("0"),
        )
        scenarios = ", ".join(
            f"{scenario}: ECL {format(amount, 'f')} com peso "
            f"{format(scenario_weight[scenario], 'f')}"
            for scenario, amount in sorted(scenario_ecl.items())
        )
        return (
            f"Execução {execution['execution_id']} (revisão {execution['revision']}, "
            f"status {execution['status']}, data-base {execution['reference_date']}) contém "
            f"{len(results)} resultados persistidos. O contrato está no Stage "
            f"{assessment['current_stage']} versus Stage {assessment['origination_stage']} na "
            f"originação, rating {assessment['current_rating']} versus "
            f"{assessment['origination_rating']}, pelos motivos "
            f"{', '.join(assessment['reason_codes'])}. ECL ponderado reconciliado: "
            f"{format(weighted, 'f')}. Cenários: {scenarios}."
        )

    def answer(self, query: AgentQuery) -> AgentResponse:
        if _has_injection(query.question):
            return AgentResponse(
                answer=(
                    "Solicitação recusada: o agente não ignora guardrails, não revela segredos "
                    "e não executa SQL, comandos ou ferramentas arbitrárias."
                ),
                citations=[],
                guardrail_status="REFUSED",
            )

        execution, results = self._execution(query.execution_id)
        if not results:
            raise ExecutionNotFoundError(f"execution without results: {query.execution_id}")
        lineage_citation = self._lineage_citation(execution)
        result_citation = self._result_citation(query.execution_id, results)
        limitation_content, limitation_citation = self._limitation()
        normalized = query.question.casefold()
        asks_conformity = any(
            term in normalized
            for term in ("conformidade", "homolog", "certific", "compliance", "aprovado")
        )
        asks_limitations = asks_conformity or any(
            term in normalized for term in ("limitação", "limitacao", "validação", "validacao")
        )

        answer = self._summary(execution, results)
        citations = [lineage_citation, result_citation, limitation_citation]
        if asks_limitations:
            rejected_components = [
                line.strip() for line in limitation_content.splitlines() if "**REJECTED**" in line
            ]
            answer += (
                " O registro versionado de limitações classifica a evidência como limitada e "
                f"mantém {len(rejected_components)} componentes com status REJECTED."
            )
        answer += (
            " Este resumo usa dados sintéticos persistidos e não atesta conformidade, "
            "homologação ou certificação oficial. "
            + " ".join(f"[{citation.citation_id}]" for citation in citations)
        )
        return AgentResponse(answer=answer, citations=citations, guardrail_status="LIMITED")
