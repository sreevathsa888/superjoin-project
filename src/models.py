"""Pydantic models shared by extraction, storage, and the UI."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class ValueType(StrEnum):
    NUMBER = "number"
    PERCENTAGE = "percentage"
    DATE = "date"
    MEASUREMENT = "measurement"
    TEXT = "text"
    ENTITY = "entity"
    EVENT = "event"
    RELATIONSHIP = "relationship"
    OTHER = "other"


class RelationshipLabel(StrEnum):
    CORROBORATED = "CORROBORATED"
    CONTRADICTION = "CONTRADICTION"
    CONTEXTUALIZED = "CONTEXTUALIZED"
    UNCERTAIN = "UNCERTAIN"
    UNRELATED = "UNRELATED"


class FactCandidate(BaseModel):
    """LLM-produced fact before source metadata is attached."""

    subject: str = Field(min_length=1, max_length=300)
    predicate: str = Field(min_length=1, max_length=300)
    value: str = Field(min_length=1, max_length=1000)
    value_type: ValueType = ValueType.OTHER
    unit: str | None = None
    time: str | None = None
    time_start: str | None = None
    time_end: str | None = None
    scope: str | None = None
    location: str | None = None
    qualifiers: dict[str, Any] = Field(default_factory=dict)
    evidence: str = Field(min_length=1, max_length=2500)
    confidence: float = Field(ge=0, le=1)
    extraction_notes: str | None = None

    @field_validator("evidence")
    @classmethod
    def evidence_must_be_nonempty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("evidence must not be empty")
        return value.strip()


class Fact(FactCandidate):
    """Grounded fact persisted in the knowledge layer."""

    fact_id: str = Field(default_factory=lambda: str(uuid4()))
    document_id: str
    source_document: str
    source_page: int = Field(ge=1)
    source_chunk: str
    normalized_value: str | None = None
    normalized_unit: str | None = None
    needs_review: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Relationship(BaseModel):
    relationship_id: str = Field(default_factory=lambda: str(uuid4()))
    fact_a_id: str
    fact_b_id: str
    relationship: RelationshipLabel
    confidence: float = Field(ge=0, le=1)
    reason: str
    context_differences: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExtractionResult(BaseModel):
    facts: list[FactCandidate] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ComparisonResult(BaseModel):
    relationship: RelationshipLabel
    confidence: float = Field(ge=0, le=1)
    reason: str
    context_differences: list[str] = Field(default_factory=list)
