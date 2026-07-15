"""Strict contracts for the grounded evidence assistant."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictAgentModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AgentQuery(StrictAgentModel):
    execution_id: str = Field(min_length=1, max_length=100)
    question: str = Field(min_length=1, max_length=1_000)


class AgentCitation(StrictAgentModel):
    citation_id: str
    source_type: Literal["execution_lineage", "execution_result", "document"]
    locator: str
    source_hash: str = Field(pattern=r"^[0-9a-f]{64}$")


class AgentResponse(StrictAgentModel):
    answer: str
    citations: list[AgentCitation]
    guardrail_status: Literal["GROUNDED", "LIMITED", "REFUSED"]
    data_classification: Literal["SYNTHETIC"] = "SYNTHETIC"
    official_conformity: Literal["NOT_ASSESSED"] = "NOT_ASSESSED"
